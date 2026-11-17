```cpp
// Core Text and Core Graphics are C APIs, so they work from C++ as they are.
// Link the CoreText and CoreGraphics frameworks.
#include <CoreText/CoreText.h>
#include <CoreGraphics/CoreGraphics.h>
#include <unordered_map>

struct Glyph {
    simd::float2 uvMin;       // top-left corner in the atlas
    simd::float2 uvMax;       // bottom-right corner
    simd::float2 size;        // quad size in pixels
    simd::float2 bearing;     // offset from the pen position to the quad's bottom-left
    float advance;
};

class FontAtlas {
public:
    MTL::Texture* texture = nullptr;
    std::unordered_map<char, Glyph> glyphs;

    FontAtlas(MTL::Device* device, const char* fontName, CGFloat fontSize, int atlasSize = 1024) {
        CFStringRef name = CFStringCreateWithCString(nullptr, fontName, kCFStringEncodingUTF8);
        CTFontRef font = CTFontCreateWithName(name, fontSize, nullptr);
        const CGFloat padding = 2;

        CGColorSpaceRef gray = CGColorSpaceCreateDeviceGray();
        CGContextRef context = CGBitmapContextCreate(nullptr, atlasSize, atlasSize, 8, atlasSize,
                                                     gray, kCGImageAlphaNone);
        CGContextSetGrayFillColor(context, 1, 1);

        CGFloat penX = 0, penY = 0, rowHeight = 0;
        const CGFloat size = atlasSize;

        for (int code = 32; code <= 126; code++) {
            UniChar character = UniChar(code);
            CGGlyph glyph = 0;
            if (!CTFontGetGlyphsForCharacters(font, &character, &glyph, 1)) continue;

            CGRect bounds;
            CGSize advance;
            CTFontGetBoundingRectsForGlyphs(font, kCTFontOrientationHorizontal, &glyph, &bounds, 1);
            CTFontGetAdvancesForGlyphs(font, kCTFontOrientationHorizontal, &glyph, &advance, 1);

            CGFloat width = std::ceil(bounds.size.width) + padding * 2;
            CGFloat height = std::ceil(bounds.size.height) + padding * 2;
            if (penX + width > size) {          // start a new row
                penX = 0;
                penY += rowHeight;
                rowHeight = 0;
            }

            // Draw so that the glyph's bounding box sits inside its cell.
            CGPoint position = CGPointMake(penX + padding - bounds.origin.x,
                                           penY + padding - bounds.origin.y);
            CTFontDrawGlyphs(font, &glyph, &position, 1, context);

            // Core Graphics has y up; texture coordinates have y down.
            glyphs[char(code)] = Glyph{
                {float(penX / size), float(1 - (penY + height) / size)},
                {float((penX + width) / size), float(1 - penY / size)},
                {float(width), float(height)},
                {float(bounds.origin.x - padding), float(bounds.origin.y - padding)},
                float(advance.width)};

            penX += width;
            rowHeight = std::max(rowHeight, height);
        }

        MTL::TextureDescriptor* descriptor = MTL::TextureDescriptor::texture2DDescriptor(
            MTL::PixelFormatR8Unorm, atlasSize, atlasSize, false);
        texture = device->newTexture(descriptor);
        texture->replaceRegion(MTL::Region::Make2D(0, 0, atlasSize, atlasSize), 0,
                               CGBitmapContextGetData(context), atlasSize);

        CGContextRelease(context);
        CGColorSpaceRelease(gray);
        CFRelease(font);
        CFRelease(name);
    }
};
```

```cpp
struct TextVertex {
    simd::float2 position;
    simd::float2 uv;
};

std::vector<TextVertex> makeVertices(const std::string& text, const FontAtlas& atlas,
                                     simd::float2 origin, float scale = 1.0f) {
    std::vector<TextVertex> vertices;
    float penX = origin.x;

    for (char character : text) {
        auto found = atlas.glyphs.find(character);
        if (found == atlas.glyphs.end()) continue;
        const Glyph& glyph = found->second;

        float x0 = penX + glyph.bearing.x * scale;
        float y0 = origin.y + glyph.bearing.y * scale;
        float x1 = x0 + glyph.size.x * scale;
        float y1 = y0 + glyph.size.y * scale;
        float u0 = glyph.uvMin.x, v0 = glyph.uvMin.y, u1 = glyph.uvMax.x, v1 = glyph.uvMax.y;

        vertices.insert(vertices.end(), {
            {{x0, y0}, {u0, v1}},
            {{x1, y0}, {u1, v1}},
            {{x1, y1}, {u1, v0}},
            {{x0, y0}, {u0, v1}},
            {{x1, y1}, {u1, v0}},
            {{x0, y1}, {u0, v0}},
        });
        penX += glyph.advance * scale;
    }
    return vertices;
}
```

```cpp
// width and height are the drawable size in pixels, from glfwGetFramebufferSize.
simd::float4x4 projection = orthographic(0, float(width), 0, float(height), -1, 1);
```

```cpp
std::vector<TextVertex> vertices = makeVertices("FPS: " + std::to_string(fps), atlas, simd::float2{20, 20});
std::memcpy(textBuffer->contents(), vertices.data(), sizeof(TextVertex) * vertices.size());

encoder->setRenderPipelineState(textPipelineState);
encoder->setVertexBuffer(textBuffer, 0, 0);
encoder->setVertexBytes(&textUniforms, sizeof(TextUniforms), 1);
encoder->setFragmentBytes(&textUniforms, sizeof(TextUniforms), 1);
encoder->setFragmentTexture(atlas.texture, 0);
encoder->setFragmentSamplerState(linearSampler, 0);
encoder->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(vertices.size()));
```
