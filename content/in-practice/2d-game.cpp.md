```cpp
struct SpriteInstance {
    simd::float2 position;
    simd::float2 size;
    simd::float4 color;
    simd::float4 uvRect = {0, 0, 1, 1};
};

class SpriteBatch {
public:
    explicit SpriteBatch(MTL::Device* device) {
        buffer = device->newBuffer(sizeof(SpriteInstance) * capacity, MTL::ResourceStorageModeShared);
        sprites.reserve(capacity);
    }

    void add(const SpriteInstance& sprite) {
        if (sprites.size() < capacity) sprites.push_back(sprite);
    }

    void flush(MTL::RenderCommandEncoder* encoder) {
        if (sprites.empty()) return;
        std::memcpy(buffer->contents(), sprites.data(), sizeof(SpriteInstance) * sprites.size());
        encoder->setVertexBuffer(buffer, 0, 0);
        encoder->drawPrimitives(MTL::PrimitiveTypeTriangleStrip, NS::UInteger(0), NS::UInteger(4),
                                NS::UInteger(sprites.size()));
        sprites.clear();
    }

private:
    static constexpr size_t capacity = 4096;
    std::vector<SpriteInstance> sprites;
    MTL::Buffer* buffer;
};
```

```cpp
const simd::float2 fieldSize = {800, 600};
simd::float4x4 projection = orthographic(0, fieldSize.x,      // left, right
                                         fieldSize.y, 0,      // bottom, top: swapped to flip y
                                         -1, 1);
```

```cpp
struct Brick {
    simd::float2 position;
    simd::float2 size;
    simd::float4 color;
    bool isAlive = true;
};

struct Ball {
    simd::float2 position;        // center
    simd::float2 velocity;
    float radius = 10;
    bool isStuck = true;          // resting on the paddle until launched
};

class Game {
public:
    simd::float2 paddlePosition = {350, 570};
    const simd::float2 paddleSize = {100, 16};
    const float paddleSpeed = 500;
    Ball ball{{400, 560}, {120, -350}};
    std::vector<Brick> bricks;
    int lives = 3;

    void loadLevel(int rows, int columns) {
        const simd::float2 size = {800.0f / columns, 24};
        const simd::float4 palette[4] = {{0.9f, 0.3f, 0.3f, 1}, {0.9f, 0.6f, 0.2f, 1},
                                         {0.3f, 0.8f, 0.4f, 1}, {0.3f, 0.5f, 0.9f, 1}};
        bricks.clear();
        for (int row = 0; row < rows; row++) {
            for (int column = 0; column < columns; column++) {
                bricks.push_back({{column * size.x, 60 + row * size.y}, size - 2.0f, palette[row % 4]});
            }
        }
    }

    void update(float deltaTime, float input, bool launch);
};
```

```cpp
void Game::update(float deltaTime, float input, bool launch) {
    // Paddle: input is -1, 0 or 1.
    paddlePosition.x += input * paddleSpeed * deltaTime;
    paddlePosition.x = std::clamp(paddlePosition.x, 0.0f, 800 - paddleSize.x);

    if (ball.isStuck) {
        ball.position = {paddlePosition.x + paddleSize.x / 2, paddlePosition.y - ball.radius};
        if (launch) ball.isStuck = false;
        return;
    }

    ball.position += ball.velocity * deltaTime;

    // Walls
    if (ball.position.x < ball.radius || ball.position.x > 800 - ball.radius) {
        ball.velocity.x = -ball.velocity.x;
        ball.position.x = std::clamp(ball.position.x, ball.radius, 800 - ball.radius);
    }
    if (ball.position.y < ball.radius) {
        ball.velocity.y = std::abs(ball.velocity.y);
    }

    // Bricks
    for (Brick& brick : bricks) {
        if (!brick.isAlive) continue;
        simd::float2 normal;
        if (collide(ball, brick.position, brick.size, normal)) {
            brick.isAlive = false;
            ball.velocity = simd::reflect(ball.velocity, normal);
            break;
        }
    }

    // Paddle: the bounce angle depends on where the ball hits.
    simd::float2 unused;
    if (ball.velocity.y > 0 && collide(ball, paddlePosition, paddleSize, unused)) {
        float center = paddlePosition.x + paddleSize.x / 2;
        float offset = (ball.position.x - center) / (paddleSize.x / 2);      // -1...1
        float speed = simd::length(ball.velocity);
        ball.velocity = simd::normalize(simd::float2{offset, -1.2f}) * speed;
    }

    // Lost the ball
    if (ball.position.y > 600 + ball.radius) {
        lives -= 1;
        ball.isStuck = true;
        ball.velocity = {120, -350};
    }
}
```

```cpp
// Returns true on overlap and writes the collision normal.
bool collide(const Ball& ball, simd::float2 rectPosition, simd::float2 rectSize, simd::float2& normal) {
    simd::float2 closest = simd::clamp(ball.position, rectPosition, rectPosition + rectSize);
    simd::float2 difference = ball.position - closest;
    if (simd::length_squared(difference) >= ball.radius * ball.radius) return false;

    // Pick the dominant axis as the collision normal.
    if (std::abs(difference.x) > std::abs(difference.y)) {
        normal = {difference.x > 0 ? 1.0f : -1.0f, 0};
    } else {
        normal = {0, difference.y > 0 ? 1.0f : -1.0f};
    }
    return true;
}
```

```cpp
void render(const Game& game, SpriteBatch& batch, MTL::RenderCommandEncoder* encoder) {
    for (const Brick& brick : game.bricks) {
        if (brick.isAlive) batch.add({brick.position, brick.size, brick.color});
    }
    batch.add({game.paddlePosition, game.paddleSize, {0.9f, 0.9f, 0.9f, 1}});
    float r = game.ball.radius;
    batch.add({game.ball.position - r, {2 * r, 2 * r}, {1, 1, 1, 1}, ballUVRect});

    encoder->setRenderPipelineState(spritePipelineState);
    encoder->setVertexBytes(&projection, sizeof(simd::float4x4), 1);
    encoder->setFragmentTexture(atlasTexture, 0);
    encoder->setFragmentSamplerState(samplerState, 0);
    batch.flush(encoder);
}
```
