/* learnmetal live demos.
 *
 * Renders small scenes with WebGL 2 and lets the reader edit the shader. The shader is
 * written in a subset of the Metal Shading Language and translated to GLSL on the fly,
 * so what you edit on the page is the same code the chapter shows.
 *
 * Supported MSL subset: structs, helper functions, one vertex and one fragment function,
 * [[stage_in]], [[buffer(n)]] (struct, scalar or pointer), [[texture(n)]] with
 * texture2d / depth2d, [[sampler(n)]], [[vertex_id]], [[instance_id]], [[front_facing]],
 * .sample(), .sample_compare(), .read(), .get_width(), .get_height(), discard_fragment().
 */
(function () {
  "use strict";

  const LM = (window.LM = window.LM || {});
  LM.demos = LM.demos || {};
  LM.define = function (id, cfg) { LM.demos[id] = cfg; };

  // ------------------------------------------------------------------ math (column-major)

  const M = (LM.math = {
    ident() { return new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]); },
    mul(a, b) {
      const o = new Float32Array(16);
      for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
        let s = 0;
        for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
        o[c * 4 + r] = s;
      }
      return o;
    },
    chain() { return Array.prototype.reduce.call(arguments, (a, b) => M.mul(a, b)); },
    translate(x, y, z) { const m = M.ident(); m[12] = x; m[13] = y; m[14] = z; return m; },
    scale(x, y, z) {
      if (y === undefined) { y = x; z = x; }
      const m = M.ident(); m[0] = x; m[5] = y; m[10] = z; return m;
    },
    rotate(angle, x, y, z) {
      const l = Math.hypot(x, y, z) || 1; x /= l; y /= l; z /= l;
      const c = Math.cos(angle), s = Math.sin(angle), t = 1 - c;
      return new Float32Array([
        c + x * x * t, y * x * t + z * s, z * x * t - y * s, 0,
        x * y * t - z * s, c + y * y * t, z * y * t + x * s, 0,
        x * z * t + y * s, y * z * t - x * s, c + z * z * t, 0,
        0, 0, 0, 1]);
    },
    /* Right-handed perspective with Metal's 0..1 depth range, as in the chapters. */
    perspective(fovY, aspect, near, far) {
      const y = 1 / Math.tan(fovY / 2), x = y / aspect, z = far / (near - far);
      return new Float32Array([x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, -1, 0, 0, z * near, 0]);
    },
    ortho(l, r, b, t, n, f) {
      return new Float32Array([2 / (r - l), 0, 0, 0, 0, 2 / (t - b), 0, 0, 0, 0, 1 / (n - f), 0,
        (l + r) / (l - r), (t + b) / (b - t), n / (n - f), 1]);
    },
    lookAt(eye, center, up) {
      const z = V.norm(V.sub(eye, center)), x = V.norm(V.cross(up, z)), y = V.cross(z, x);
      return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
        -V.dot(x, eye), -V.dot(y, eye), -V.dot(z, eye), 1]);
    },
    /* Inverse transpose of the upper-left 3x3: the cofactor matrix divided by the determinant. */
    normalMatrix(m) {
      const a = (r, c) => m[c * 4 + r];
      const cof = (r, c) => {
        const r1 = (r + 1) % 3, r2 = (r + 2) % 3, c1 = (c + 1) % 3, c2 = (c + 2) % 3;
        return a(r1, c1) * a(r2, c2) - a(r1, c2) * a(r2, c1);
      };
      const det = a(0, 0) * cof(0, 0) + a(0, 1) * cof(0, 1) + a(0, 2) * cof(0, 2) || 1;
      const o = new Float32Array(9);
      for (let c = 0; c < 3; c++) for (let r = 0; r < 3; r++) o[c * 3 + r] = cof(r, c) / det;
      return o;
    },
  });

  const V = (LM.vec = {
    sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
    add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
    mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
    dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
    cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
    norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
  });

  // ------------------------------------------------------------------ meshes
  // Interleaved: position 3, normal 3, uv 2, color 3, tangent 3 (attributes 0 to 4).

  const STRIDE = 14;
  const meshBuilders = {
    cube() {
      const faces = [[[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],
        [[1, 0, 0], [0, 0, -1], [0, 1, 0]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
        [[0, 1, 0], [1, 0, 0], [0, 0, -1]], [[0, -1, 0], [1, 0, 0], [0, 0, 1]]];
      const corners = [[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]];
      const d = [];
      for (const [n, r, u] of faces) for (const c of corners) {
        for (let i = 0; i < 3; i++) d.push((n[i] + r[i] * c[0] + u[i] * c[1]) * 0.5);
        d.push(n[0], n[1], n[2], c[0] * 0.5 + 0.5, 0.5 - c[1] * 0.5,
          n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, r[0], r[1], r[2]);
      }
      return d;
    },
    plane() {      // 1 x 1 in the xz plane, facing up; scale it with the model matrix
      const p = [[-0.5, 0, 0.5, 0, 1], [0.5, 0, 0.5, 1, 1], [0.5, 0, -0.5, 1, 0], [-0.5, 0, -0.5, 0, 0]];
      const d = [];
      for (const i of [0, 1, 2, 0, 2, 3]) d.push(p[i][0], 0, p[i][2], 0, 1, 0, p[i][3], p[i][4], 1, 1, 1, 1, 0, 0);
      return d;
    },
    floor() {      // like plane, with texture coordinates that repeat 8 times
      return meshBuilders.plane().map((v, i) => (i % STRIDE === 6 || i % STRIDE === 7 ? v * 8 : v));
    },
    quad() {       // the textured rectangle of the first chapters, in the xy plane
      const p = [[0.5, 0.5, 1, 0, 1, 0, 0], [0.5, -0.5, 1, 1, 0, 1, 0], [-0.5, -0.5, 0, 1, 0, 0, 1], [-0.5, 0.5, 0, 0, 1, 1, 0]];
      const d = [];
      for (const i of [0, 1, 3, 1, 2, 3]) d.push(p[i][0], p[i][1], 0, 0, 0, 1, p[i][2], p[i][3], p[i][4], p[i][5], p[i][6], 1, 0, 0);
      return d;
    },
    triangle() {
      const p = [[-0.5, -0.5, 1, 0, 0], [0.5, -0.5, 0, 1, 0], [0, 0.5, 0, 0, 1]];
      const d = [];
      for (const v of p) d.push(v[0], v[1], 0, 0, 0, 1, v[0] + 0.5, 0.5 - v[1], v[2], v[3], v[4], 1, 0, 0);
      return d;
    },
    sphere() {     // radius 0.5
      const seg = 40, d = [];
      const vert = (i, j) => {
        const th = (i / seg) * Math.PI, ph = (j / seg) * 2 * Math.PI;
        const n = [Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)];
        return [n[0] * 0.5, n[1] * 0.5, n[2] * 0.5, n[0], n[1], n[2], j / seg, i / seg,
          n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, -Math.sin(ph), 0, Math.cos(ph)];
      };
      for (let i = 0; i < seg; i++) for (let j = 0; j < seg; j++) {
        const a = vert(i, j), b = vert(i + 1, j), c = vert(i + 1, j + 1), e = vert(i, j + 1);
        d.push(...a, ...c, ...b, ...a, ...e, ...c);
      }
      return d;
    },
  };

  // ------------------------------------------------------------------ MSL -> GLSL

  const GLSL_HEAD = "#version 300 es\nprecision highp float;\nprecision highp int;\nprecision highp sampler2DShadow;\n" +
    "uniform float lm_flipY;\nuniform float lm_height;\n" +
    "float saturate(float x){return clamp(x,0.0,1.0);} vec2 saturate(vec2 x){return clamp(x,0.0,1.0);} " +
    "vec3 saturate(vec3 x){return clamp(x,0.0,1.0);} vec4 saturate(vec4 x){return clamp(x,0.0,1.0);}\n";
  const HEAD_LINES = GLSL_HEAD.split("\n").length - 1;

  function closeIndex(s, i, open, close) {
    let depth = 0;
    for (; i < s.length; i++) {
      if (s[i] === open) depth++;
      else if (s[i] === close && --depth === 0) return i;
    }
    return -1;
  }

  function splitArgs(s) {
    const out = [];
    let depth = 0, start = 0;
    for (let i = 0; i < s.length; i++) {
      const ch = s[i];
      if (ch === "(" || ch === "[" || ch === "<") depth++;
      else if (ch === ")" || ch === "]" || ch === ">") depth--;
      else if (ch === "," && depth === 0) { out.push(s.slice(start, i)); start = i + 1; }
    }
    if (s.slice(start).trim()) out.push(s.slice(start));
    return out.map((a) => a.trim());
  }

  const keepLines = (s) => s.replace(/[^\n]/g, "");

  function mapTypes(s) {
    return s
      .replace(/\b(?:float|half)([234])x\1\b/g, "mat$1")
      .replace(/\b(?:float|half)([234])\b/g, "vec$1")
      .replace(/\buint([234])\b/g, "uvec$1")
      .replace(/\bint([234])\b/g, "ivec$1")
      .replace(/\bhalf\b/g, "float");
  }

  function rewriteMethod(s, method, fn) {
    const re = new RegExp("([A-Za-z_][\\w.\\[\\]]*)\\.(" + method + ")\\s*\\(", "g");
    let m, out = "", last = 0;
    while ((m = re.exec(s))) {
      const open = m.index + m[0].length - 1;
      const end = closeIndex(s, open, "(", ")");
      if (end < 0) break;
      out += s.slice(last, m.index) + fn(m[1], splitArgs(s.slice(open + 1, end)));
      last = end + 1;
      re.lastIndex = last;
    }
    return out + s.slice(last);
  }

  function parseStructs(code) {
    const structs = {};
    const re = /struct\s+(\w+)\s*\{([^}]*)\}/g;
    let m;
    while ((m = re.exec(code))) {
      structs[m[1]] = m[2].split(";").map((x) => x.trim()).filter(Boolean).map((decl) => {
        const attr = /\[\[\s*([\w]+)(?:\((\w+)\))?/.exec(decl);
        const core = decl.replace(/\[\[.*?\]\]/g, "").trim();
        const mm = /^(.*\S)\s+(\w+)$/.exec(core);
        return mm && { type: mm[1], name: mm[2], attr: attr && attr[1], arg: attr && attr[2] };
      }).filter(Boolean);
    }
    return structs;
  }

  /* Returns { vs, fs } GLSL sources, or throws an Error with a readable message. */
  function translate(src, opts) {
    opts = opts || {};
    let code = src.replace(/\/\/[^\n]*|\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, " "));
    code = code.replace(/^[ \t]*#include[^\n]*|^[ \t]*using namespace[^\n]*/gm, "");
    const structs = parseStructs(code);

    const entries = [];
    const buffers = [];          // every [[buffer(n)]] parameter, for the automatic controls
    const re = /\b(vertex|fragment)\s+(\w+)\s+(\w+)\s*\(/g;
    let m;
    while ((m = re.exec(code))) {
      const open = m.index + m[0].length - 1;
      const close = closeIndex(code, open, "(", ")");
      const bodyStart = code.indexOf("{", close);
      const bodyEnd = closeIndex(code, bodyStart, "{", "}");
      if (close < 0 || bodyStart < 0 || bodyEnd < 0) throw new Error("Could not find the body of " + m[3] + "().");
      entries.push({ stage: m[1], ret: m[2], name: m[3], start: m.index, bodyStart, bodyEnd,
        params: splitArgs(code.slice(open + 1, close)) });
    }
    const pick = (stage, wanted) => entries.find((e) => e.stage === stage && (!wanted || e.name === wanted));
    const vs = pick("vertex", opts.vertex), fs = pick("fragment", opts.fragment);
    if (!vs) throw new Error("No vertex function found.");
    if (!fs) throw new Error("No fragment function found.");

    function entryText(e) {
      const tag = e.stage === "vertex" ? "lm_vs_" : "lm_fs_";
      const globals = [], renames = [];
      let stageIn = null;
      for (const p of e.params) {
        const attr = (/\[\[\s*(\w+)/.exec(p) || [])[1];
        const core = p.replace(/\[\[.*?\]\]/g, "").trim();
        const name = (/(\w+)\s*$/.exec(core) || [])[1];
        if (attr === "stage_in") {
          stageIn = core.split(/\s+/)[0];
          globals.push(stageIn + " lm_in;");
          renames.push([name, "lm_in"]);
        } else if (attr === "buffer") {
          const b = /^(?:constant|const\s+device|device)\s+(\w+)\s*([&*])\s*(\w+)$/.exec(core);
          if (!b) throw new Error("Unsupported buffer parameter: " + core);
          globals.push("uniform " + b[1] + " " + tag + b[3] + (b[2] === "*" ? "[" + (opts.arraySize || 8) + "]" : "") + ";");
          renames.push([b[3], tag + b[3]]);
          buffers.push({ type: b[1], name: b[3], pointer: b[2] === "*" });
        } else if (attr === "texture") {
          const t = /^(\w+)\s*<[^>]*>\s+(\w+)$/.exec(core);
          const kind = t && { texture2d: "sampler2D", depth2d: "sampler2DShadow", texturecube: "samplerCube" }[t[1]];
          if (!kind) throw new Error("Unsupported texture parameter: " + core);
          globals.push("uniform " + kind + " " + t[2] + ";");
        } else if (attr === "sampler") {
          /* samplers are part of the texture object in WebGL */
        } else if (attr === "vertex_id") renames.push([name, "uint(gl_VertexID)"]);
        else if (attr === "instance_id") renames.push([name, "uint(gl_InstanceID)"]);
        else if (attr === "front_facing") renames.push([name, "gl_FrontFacing"]);
        else throw new Error("Unsupported parameter in " + e.name + "(): " + p);
      }
      let body = code.slice(e.bodyStart, e.bodyEnd + 1);
      for (const [from, to] of renames) body = body.replace(new RegExp("(?<![\\w.])" + from + "\\b", "g"), to);
      const head = globals.join(" ") + " " + e.ret + " " + e.name + "()";
      return { text: head + keepLines(code.slice(e.start, e.bodyStart)) + body, stageIn };
    }

    function stageSource(e, other) {
      const t = entryText(e);
      const ranges = entries.filter((x) => x !== e).map((x) => [x.start, x.bodyEnd + 1, keepLines(code.slice(x.start, x.bodyEnd + 1))]);
      ranges.push([e.start, e.bodyEnd + 1, t.text]);
      ranges.sort((a, b) => b[0] - a[0]);
      let s = code;
      for (const [a, b, text] of ranges) s = s.slice(0, a) + text + s.slice(b);

      s = s.replace(/\[\[.*?\]\]/g, "")
        .replace(/\bconstexpr\s+sampler\b[^;]*;/g, "")                       // samplers live in the texture in WebGL
        .replace(/\btexture2d\s*<[^>]*>/g, "sampler2D").replace(/\bdepth2d\s*<[^>]*>/g, "sampler2DShadow")
        .replace(/\b([A-Z]\w*|float[234]?|int|uint|bool)\s+&(\w+)\b/g, "inout $1 $2");   // reference parameters
      s = mapTypes(s)
        .replace(/\bstatic\s+/g, "")
        .replace(/\b(?:constexpr|constant)\b/g, "const")
        .replace(/\bout\b/g, "lm_out")
        .replace(/\bdiscard_fragment\s*\(\s*\)/g, "discard")
        .replace(/\bdfdx\b/g, "dFdx").replace(/\bdfdy\b/g, "dFdy")
        .replace(/\batan2\b/g, "atan").replace(/\bfmod\b/g, "mod").replace(/\brsqrt\b/g, "inversesqrt")
        .replace(/\bconst\s+(\w+)\s+(\w+)\s*\[(\d+)\]\s*=\s*\{([^}]*)\}/g, "const $1 $2[$3] = $1[$3]($4)");
      s = rewriteMethod(s, "sample_compare", (o, a) => "texture(" + o + ", vec3(" + a[1] + ", " + a[2] + "))");
      s = rewriteMethod(s, "sample", (o, a) => {
        const lod = a[2] && /^level\s*\((.*)\)$/.exec(a[2]);
        return lod ? "textureLod(" + o + ", " + a[1] + ", " + lod[1] + ")" : "texture(" + o + ", " + a[1] + ")";
      });
      s = rewriteMethod(s, "read", (o, a) => "texelFetch(" + o + ", ivec2(" + a[0] + "), 0)");
      s = rewriteMethod(s, "get_width", (o) => "float(textureSize(" + o + ", 0).x)");
      s = rewriteMethod(s, "get_height", (o) => "float(textureSize(" + o + ", 0).y)");

      let head = GLSL_HEAD, main = "\nvoid main() {\n";
      const outStruct = structs[vs.ret];
      const varyings = (outStruct || []).filter((f) => f.attr !== "position");
      if (e.stage === "vertex") {
        for (const f of (t.stageIn && structs[t.stageIn]) || []) {
          head += "layout(location=" + (f.arg || 0) + ") in " + mapTypes(f.type) + " lm_a_" + f.name + "; ";
          main += "  lm_in." + f.name + " = lm_a_" + f.name + ";\n";
        }
        for (const f of varyings) head += "out " + mapTypes(f.type) + " lm_v_" + f.name + "; ";
        if (outStruct) {
          const pos = outStruct.find((f) => f.attr === "position");
          if (!pos) throw new Error(vs.ret + " needs a member marked [[position]].");
          main += "  " + vs.ret + " o = " + e.name + "();\n  vec4 p = o." + pos.name + ";\n";
          for (const f of varyings) main += "  lm_v_" + f.name + " = o." + f.name + ";\n";
        } else {
          main += "  vec4 p = " + e.name + "();\n";
        }
        /* Metal clip space has z from 0 to w; OpenGL's runs from -w to w. */
        main += "  gl_Position = vec4(p.x, p.y * lm_flipY, p.z * 2.0 - p.w, p.w);\n}\n";
      } else {
        head += "out vec4 lm_fragColor; ";
        for (const f of varyings) head += "in " + mapTypes(f.type) + " lm_v_" + f.name + "; ";
        if (t.stageIn) {
          for (const f of structs[t.stageIn] || []) {
            main += f.attr === "position"
              ? "  lm_in." + f.name + " = vec4(gl_FragCoord.x, lm_flipY > 0.0 ? lm_height - gl_FragCoord.y : gl_FragCoord.y, gl_FragCoord.z, gl_FragCoord.w);\n"
              : "  lm_in." + f.name + " = lm_v_" + f.name + ";\n";
          }
        }
        main += "  lm_fragColor = " + e.name + "();\n}\n";
      }
      return head + "\n" + s + main;
    }

    const out = { vs: stageSource(vs, fs), fs: stageSource(fs, vs), headLines: HEAD_LINES + 1 };

    /* Plain values the shader receives: the members of each uniform struct, or a bare scalar. */
    const SIMPLE = /^(?:float|half|int|uint|bool|(?:float|half)[234])$/;
    const fields = {};
    for (const b of buffers) {
        if (b.pointer) continue;
        if (structs[b.type]) {
            for (const f of structs[b.type]) if (SIMPLE.test(f.type)) fields[f.name] = f.type.replace("half", "float");
        } else if (SIMPLE.test(b.type)) {
            fields[b.name] = b.type.replace("half", "float");
        }
    }
    out.fields = fields;
    return out;
  }
  LM.translate = translate;

  // ------------------------------------------------------------------ hidden helper shaders (MSL)

  const HELPER_SRC = `
struct VertexIn { float3 position [[attribute(0)]]; };
struct Plain { float4 position [[position]]; };
struct Uniforms { float4x4 model; float4x4 view; float4x4 projection; float4x4 lightViewProjection; };
struct Lamp { float3 color; };
vertex Plain vertex_lamp(VertexIn in [[stage_in]], constant Uniforms &uniforms [[buffer(1)]]) {
    Plain out;
    out.position = uniforms.projection * uniforms.view * uniforms.model * float4(in.position, 1.0);
    return out;
}
vertex Plain vertex_depth(VertexIn in [[stage_in]], constant Uniforms &uniforms [[buffer(1)]]) {
    Plain out;
    out.position = uniforms.lightViewProjection * uniforms.model * float4(in.position, 1.0);
    return out;
}
fragment float4 fragment_lamp(Plain in [[stage_in]], constant Lamp &lamp [[buffer(1)]]) {
    return float4(lamp.color, 1.0);
}
fragment float4 fragment_depth(Plain in [[stage_in]]) {
    return float4(1.0);
}`;

  // ------------------------------------------------------------------ GL helpers

  function compile(gl, type, source) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, source);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      const log = gl.getShaderInfoLog(sh) || "Shader failed to compile.";
      gl.deleteShader(sh);
      const err = new Error(log);
      err.glsl = true;
      throw err;
    }
    return sh;
  }

  function buildProgram(gl, src, opts) {
    const t = translate(src, opts);
    const vs = compile(gl, gl.VERTEX_SHADER, t.vs), fs = compile(gl, gl.FRAGMENT_SHADER, t.fs);
    const p = gl.createProgram();
    gl.attachShader(p, vs); gl.attachShader(p, fs);
    gl.linkProgram(p);
    gl.deleteShader(vs); gl.deleteShader(fs);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      const log = gl.getProgramInfoLog(p) || "Program failed to link.";
      gl.deleteProgram(p);
      throw new Error(log);
    }
    const uniforms = [];
    const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) {
      const info = gl.getActiveUniform(p, i);
      const name = info.name.replace(/\[0\]$/, "");
      let key = name.replace(/^lm_[vf]s_/, "");
      const dot = key.indexOf(".");
      if (dot > 0 && key.slice(0, dot).indexOf("[") < 0 && name !== key) key = key.slice(dot + 1);
      uniforms.push({ key, type: info.type, size: info.size, loc: gl.getUniformLocation(p, info.name) });
    }
    return { program: p, uniforms, headLines: t.headLines, fields: t.fields };
  }

  function applyUniforms(gl, prog, values, textures) {
    let unit = 0;
    for (const u of prog.uniforms) {
      const T = u.type;
      if (T === gl.SAMPLER_2D || T === gl.SAMPLER_2D_SHADOW) {
        const tex = textures[u.key];
        gl.activeTexture(gl.TEXTURE0 + unit);
        gl.bindTexture(gl.TEXTURE_2D, tex || textures.__white);
        gl.uniform1i(u.loc, unit++);
        continue;
      }
      let v = values[u.key];
      if (v === undefined) continue;
      if (typeof v === "boolean") v = v ? 1 : 0;
      if (T === gl.FLOAT) gl.uniform1f(u.loc, v);
      else if (T === gl.FLOAT_VEC2) gl.uniform2fv(u.loc, v);
      else if (T === gl.FLOAT_VEC3) gl.uniform3fv(u.loc, v);
      else if (T === gl.FLOAT_VEC4) gl.uniform4fv(u.loc, v);
      else if (T === gl.FLOAT_MAT3) gl.uniformMatrix3fv(u.loc, false, v);
      else if (T === gl.FLOAT_MAT4) gl.uniformMatrix4fv(u.loc, false, v);
      else if (T === gl.INT || T === gl.BOOL) gl.uniform1i(u.loc, v);
      else if (T === gl.UNSIGNED_INT) gl.uniform1ui(u.loc, v);
    }
  }

  function readableError(err, headLines, preludeLines) {
    let msg = String(err.message || err).trim();
    if (!err.glsl) return msg;
    const lines = msg.split("\n").filter(Boolean).slice(0, 4).map((line) => {
      const m = /ERROR:\s*\d+:(\d+):\s*(.*)/.exec(line);
      if (!m) return line;
      const srcLine = +m[1] - headLines - preludeLines;
      const text = m[2].replace(/lm_[vf]s_/g, "").replace(/lm_in\b/g, "in").replace(/lm_out\b/g, "out")
        .replace(/\bvec([234])\b/g, "float$1").replace(/\bmat([234])\b/g, "float$1x$1");
      return (srcLine > 0 ? "Line " + srcLine + ": " : "In the hidden part of the shader: ") + text;
    });
    msg = lines.join("\n");
    if (/cannot convert|wrong operand types|no matching overloaded/.test(msg)) {
      msg += "\nHint: the browser's compiler is stricter than Metal about mixing int and float. Write 2.0, not 2.";
    }
    return msg;
  }

  // ------------------------------------------------------------------ code editor

  const KEYWORDS = /^(?:struct|return|if|else|for|while|const|constant|static|vertex|fragment|kernel|using|namespace|discard_fragment|true|false|break|continue)$/;
  const TYPES = /^(?:void|bool|int|uint|float|half|(?:float|half|int|uint)[234](?:x[234])?|texture2d|depth2d|texturecube|sampler|VertexIn|VertexOut)$/;

  function highlight(code) {
    const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    return code.replace(/(\/\/[^\n]*)|(\[\[.*?\]\])|(\b\d+\.?\d*(?:e[-+]?\d+)?[fh]?\b)|([A-Za-z_]\w*)|([^])/g,
      (m, comment, attr, num, word) => {
        if (comment) return '<i class="c">' + esc(comment) + "</i>";
        if (attr) return '<i class="a">' + esc(attr) + "</i>";
        if (num) return '<i class="n">' + num + "</i>";
        if (word) return KEYWORDS.test(word) ? '<i class="k">' + word + "</i>" : TYPES.test(word) ? '<i class="t">' + word + "</i>" : word;
        return esc(m);
      });
  }

  function makeEditor(parent, text, onChange) {
    const wrap = document.createElement("div");
    wrap.className = "lm-editor";
    wrap.innerHTML = '<pre aria-hidden="true"><code></code></pre><textarea spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off" aria-label="Shader source"></textarea>';
    const pre = wrap.firstChild, codeEl = pre.firstChild, ta = wrap.lastChild;
    const paint = () => { codeEl.innerHTML = highlight(ta.value) + "\n"; };
    ta.value = text;
    paint();
    ta.addEventListener("input", () => { paint(); onChange(ta.value); });
    ta.addEventListener("scroll", () => { pre.scrollTop = ta.scrollTop; pre.scrollLeft = ta.scrollLeft; });
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const s = ta.selectionStart;
        ta.setRangeText("    ", s, ta.selectionEnd, "end");
        paint(); onChange(ta.value);
      }
    });
    parent.appendChild(wrap);
    return { set(v) { ta.value = v; paint(); onChange(v); } };
  }

  // ------------------------------------------------------------------ controls

  function hexToRgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }

  function buildControls(parent, controls, state, onChange) {
    if (!controls || !controls.length) return;
    const box = document.createElement("div");
    box.className = "lm-controls";
    for (const c of controls) {
      const label = document.createElement("label");
      const name = document.createElement("span");
      name.textContent = c.label;
      label.appendChild(name);
      let input;
      if (c.type === "select") {
        input = document.createElement("select");
        for (const [value, text] of c.options) {
          const o = document.createElement("option");
          o.value = value; o.textContent = text;
          input.appendChild(o);
        }
        input.value = c.value;
        state[c.id] = c.value;
        input.addEventListener("change", () => { state[c.id] = input.value; onChange(); });
      } else if (c.type === "check") {
        input = document.createElement("input");
        input.type = "checkbox"; input.checked = !!c.value;
        state[c.id] = !!c.value;
        label.classList.add("lm-check");
        input.addEventListener("change", () => { state[c.id] = input.checked; onChange(); });
      } else if (c.type === "color") {
        input = document.createElement("input");
        input.type = "color"; input.value = c.value;
        state[c.id] = hexToRgb(c.value);
        input.addEventListener("input", () => { state[c.id] = hexToRgb(input.value); onChange(); });
      } else {
        input = document.createElement("input");
        input.type = "range"; input.min = c.min; input.max = c.max; input.step = c.step || 0.01; input.value = c.value;
        state[c.id] = c.value;
        const out = document.createElement("output");
        const show = () => { out.textContent = (+input.value).toFixed(c.step >= 1 ? 0 : 2); };
        show();
        input.addEventListener("input", () => { state[c.id] = +input.value; show(); onChange(); });
        label.appendChild(input);
        label.appendChild(out);
        box.appendChild(label);
        continue;
      }
      label.appendChild(input);
      box.appendChild(label);
    }
    parent.appendChild(box);
  }

  // ------------------------------------------------------------------ the demo

  function mount(el) {
    const cfg = LM.demos[el.dataset.demo];
    if (!cfg || el.dataset.ready) return;
    el.dataset.ready = "1";
    el.classList.add("lm-demo");
    const state = {};
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

    const stage = document.createElement("div");
    stage.className = "lm-stage";
    el.appendChild(stage);

    if (cfg.custom) {              // demos that draw themselves (2D canvas)
      const canvas = document.createElement("canvas");
      canvas.style.aspectRatio = String(cfg.aspect || 16 / 9);
      if (cfg.maxWidth) canvas.style.maxWidth = cfg.maxWidth + "px";
      stage.appendChild(canvas);
      buildControls(el, cfg.controls, state, () => api.redraw && api.redraw());
      const api = cfg.custom(canvas, state) || {};
      addCaption(el, cfg);
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.style.aspectRatio = String(cfg.aspect || 16 / 9);
    if (cfg.maxWidth) canvas.style.maxWidth = cfg.maxWidth + "px";
    canvas.tabIndex = 0;
    stage.appendChild(canvas);
    const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, powerPreference: "low-power" });
    if (!gl) {
      stage.innerHTML = el.dataset.fallback
        ? '<img src="' + el.dataset.fallback + '" alt="">'
        : '<p class="lm-nogl">This live demo needs WebGL 2, which this browser does not provide.</p>';
      addCaption(el, cfg);
      return;
    }

    let dirty = true;
    const touch = () => { dirty = true; };
    buildControls(el, cfg.controls, state, touch);

    /* Controls for values the reader adds to a uniform struct in the editor. */
    const autoBox = document.createElement("div");
    autoBox.className = "lm-controls lm-auto";
    autoBox.hidden = true;
    el.appendChild(autoBox);
    const autoValues = {}, autoRows = {};
    let autoPending = null;

    function autoControl(key, type) {
      const row = document.createElement("label");
      const name = document.createElement("span");
      name.textContent = key;
      row.appendChild(name);
      const number = (value, step, onInput) => {
        const input = document.createElement("input");
        input.type = "number"; input.step = step; input.value = value;
        input.addEventListener("input", () => { onInput(parseFloat(input.value) || 0); touch(); });
        row.appendChild(input);
        return input;
      };
      const n = +type.slice(-1);
      if (type === "bool") {
        const input = document.createElement("input");
        input.type = "checkbox";
        autoValues[key] = false;
        input.addEventListener("change", () => { autoValues[key] = input.checked; touch(); });
        row.classList.add("lm-check");
        row.appendChild(input);
      } else if (type === "int" || type === "uint") {
        autoValues[key] = 0;
        number(0, 1, (v) => { autoValues[key] = Math.round(v); });
      } else if (type === "float") {
        autoValues[key] = 0.5;
        const range = document.createElement("input");
        range.type = "range"; range.min = 0; range.max = 1; range.step = 0.01; range.value = 0.5;
        row.appendChild(range);
        const box = number(0.5, 0.01, (v) => { autoValues[key] = v; range.value = v; });   // type any value here
        range.addEventListener("input", () => { autoValues[key] = +range.value; box.value = range.value; touch(); });
      } else if (n >= 3 && /colou?r|albedo|tint|emissi/i.test(key)) {
        autoValues[key] = n === 4 ? [1, 1, 1, 1] : [1, 1, 1];
        const input = document.createElement("input");
        input.type = "color"; input.value = "#ffffff";
        input.addEventListener("input", () => { autoValues[key] = hexToRgb(input.value).concat(n === 4 ? [1] : []); touch(); });
        row.appendChild(input);
      } else {
        autoValues[key] = new Array(n).fill(0);
        for (let i = 0; i < n; i++) number(0, 0.1, (v) => { autoValues[key][i] = v; });
      }
      row.dataset.type = type;
      return row;
    }

    /* Show a control for every field that neither the demo nor the engine supplies. */
    function syncAutoControls(fields, known) {
      for (const key in autoRows) {
        if (fields[key] !== autoRows[key].dataset.type || known.has(key)) {
          autoRows[key].remove();
          delete autoRows[key];
          delete autoValues[key];
        }
      }
      for (const key in fields) {
        if (known.has(key) || autoRows[key]) continue;
        autoRows[key] = autoControl(key, fields[key]);
        autoBox.appendChild(autoRows[key]);
      }
      autoBox.hidden = !Object.keys(autoRows).length;
    }

    // --- GPU resources
    const meshes = {};
    function mesh(name) {
      if (meshes[name]) return meshes[name];
      const data = new Float32Array(meshBuilders[name]());
      const vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      [[0, 3, 0], [1, 3, 3], [2, 2, 6], [3, 3, 8], [4, 3, 11]].forEach(([loc, size, off]) => {
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, size, gl.FLOAT, false, STRIDE * 4, off * 4);
      });
      return (meshes[name] = { vao, count: data.length / STRIDE });
    }
    const emptyVao = gl.createVertexArray();

    const textures = {};
    function pixelTexture(rgba) {
      const t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(rgba));
      return t;
    }
    textures.__white = pixelTexture([255, 255, 255, 255]);
    const imageTextures = [];
    for (const [name, id] of Object.entries(cfg.textures || {})) {
      const t = pixelTexture([128, 128, 128, 255]);
      textures[name] = t;
      imageTextures.push(t);
      const img = new Image();
      img.onload = () => {
        gl.bindTexture(gl.TEXTURE_2D, t);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);       // row 0 is the top, as in Metal
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        gl.generateMipmap(gl.TEXTURE_2D);
        touch();
      };
      img.src = (LM.textures || {})[id] || id;
    }

    function target(w, h, depthOnly) {
      const fb = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
      const out = { fb, w, h };
      const depth = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, depth);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.DEPTH_COMPONENT24, w, h, 0, gl.DEPTH_COMPONENT, gl.UNSIGNED_INT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, depthOnly ? gl.LINEAR : gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, depthOnly ? gl.LINEAR : gl.NEAREST);
      if (depthOnly) {
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_COMPARE_MODE, gl.COMPARE_REF_TO_TEXTURE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_COMPARE_FUNC, gl.LEQUAL);
      }
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, depth, 0);
      out.depth = depth;
      if (depthOnly) {
        gl.drawBuffers([gl.NONE]);
        gl.readBuffer(gl.NONE);
      } else {
        const color = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, color);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, color, 0);
        out.color = color;
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      return out;
    }

    // --- programs
    const prelude = cfg.prelude ? cfg.prelude.replace(/^\n/, "") : "";
    const preludeLines = prelude ? prelude.split("\n").length : 0;
    const full = (code) => (prelude ? prelude + "\n" : "") + code;
    const lampProgram = buildProgram(gl, HELPER_SRC, { vertex: "vertex_lamp", fragment: "fragment_lamp" });
    const depthProgram = cfg.shadow ? buildProgram(gl, HELPER_SRC, { vertex: "vertex_depth", fragment: "fragment_depth" }) : null;
    const sceneProgram = cfg.sceneSource ? buildProgram(gl, cfg.sceneSource) : null;
    const backProgram = cfg.backgroundSource ? buildProgram(gl, cfg.backgroundSource) : null;
    const shadowTarget = cfg.shadow ? target(1024, 1024, true) : null;
    let sceneTarget = null;
    let program = null;

    // --- code panel
    const errorBox = document.createElement("pre");
    errorBox.className = "lm-error";
    errorBox.hidden = true;
    let status = null;

    function rebuild(code) {
      try {
        const next = buildProgram(gl, full(code), cfg.entry);
        if (program) gl.deleteProgram(program.program);
        program = next;
        autoPending = next.fields;
        errorBox.hidden = true;
        if (status) { status.textContent = "Compiled"; status.className = "lm-status ok"; }
      } catch (err) {
        errorBox.textContent = readableError(err, HEAD_LINES + 1, preludeLines);
        errorBox.hidden = false;
        if (status) { status.textContent = "Error"; status.className = "lm-status bad"; }
      }
      touch();
    }

    if (cfg.code && cfg.editable !== false) {
      const panel = document.createElement("div");
      panel.className = "lm-code";
      const bar = document.createElement("div");
      bar.className = "lm-bar";
      const title = document.createElement("span");
      title.className = "lm-file";
      title.textContent = "Shaders.metal";
      status = document.createElement("span");
      const reset = document.createElement("button");
      reset.type = "button"; reset.textContent = "Reset";
      bar.append(title, status, reset);
      panel.appendChild(bar);
      let timer = 0;
      const editor = makeEditor(panel, cfg.code.replace(/^\n/, ""), (v) => {
        clearTimeout(timer);
        timer = setTimeout(() => rebuild(v), 200);
      });
      reset.addEventListener("click", () => editor.set(cfg.code.replace(/^\n/, "")));
      panel.appendChild(errorBox);
      if (prelude) {
        const d = document.createElement("details");
        d.className = "lm-prelude";
        d.innerHTML = "<summary>Show the structs and the vertex function</summary><pre><code></code></pre>";
        d.querySelector("code").innerHTML = highlight(prelude);
        panel.appendChild(d);
      }
      if (el.dataset.collapse) {            // compact form: the editor sits behind a disclosure
        const d = document.createElement("details");
        d.className = "lm-details";
        const sum = document.createElement("summary");
        sum.textContent = "Edit the shader";
        d.append(sum, panel);
        el.appendChild(d);
      } else {
        el.appendChild(panel);
      }
    } else {
      el.appendChild(errorBox);
    }
    rebuild((cfg.code || "").replace(/^\n/, ""));
    addCaption(el, cfg);

    // --- camera
    const cam = Object.assign({ eye: [0, 0, 3], target: [0, 0, 0], fov: 45, mode: "orbit" }, cfg.camera);
    const off = V.sub(cam.eye, cam.target);
    let radius = Math.hypot(off[0], off[1], off[2]);
    let yaw = Math.atan2(off[0], off[2]), pitch = Math.asin(off[1] / radius);
    let flyPos = cam.eye.slice(), flyYaw = Math.atan2(-off[0], -off[2]), flyPitch = -pitch;
    const keys = {};
    let drag = null;
    if (cam.mode !== "fixed") {
      canvas.classList.add("lm-grab");
      canvas.addEventListener("pointerdown", (e) => { drag = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId); });
      canvas.addEventListener("pointerup", () => { drag = null; });
      canvas.addEventListener("pointercancel", () => { drag = null; });
      canvas.addEventListener("pointermove", (e) => {
        if (!drag) return;
        const dx = e.clientX - drag[0], dy = e.clientY - drag[1];
        drag = [e.clientX, e.clientY];
        if (cam.mode === "fly") {
          flyYaw -= dx * 0.005;
          flyPitch = Math.max(-1.5, Math.min(1.5, flyPitch - dy * 0.005));
        } else {
          yaw -= dx * 0.008;
          pitch = Math.max(-1.5, Math.min(1.5, pitch + dy * 0.008));
        }
        touch();
      });
    }
    if (cam.mode === "fly") {
      canvas.addEventListener("keydown", (e) => {
        const k = e.key.toLowerCase();
        if ("wasdqe".indexOf(k) >= 0) { keys[k] = true; e.preventDefault(); }
      });
      canvas.addEventListener("keyup", (e) => { keys[e.key.toLowerCase()] = false; });
      canvas.addEventListener("blur", () => { for (const k in keys) keys[k] = false; });
    }

    function cameraState(dt) {
      if (cam.mode === "fly") {
        const front = [Math.sin(flyYaw) * Math.cos(flyPitch), Math.sin(flyPitch), Math.cos(flyYaw) * Math.cos(flyPitch)];
        const right = V.norm(V.cross(front, [0, 1, 0]));
        const sp = 3 * dt;
        if (keys.w) flyPos = V.add(flyPos, V.mul(front, sp));
        if (keys.s) flyPos = V.add(flyPos, V.mul(front, -sp));
        if (keys.d) flyPos = V.add(flyPos, V.mul(right, sp));
        if (keys.a) flyPos = V.add(flyPos, V.mul(right, -sp));
        if (keys.e) flyPos[1] += sp;
        if (keys.q) flyPos[1] -= sp;
        if (keys.w || keys.a || keys.s || keys.d || keys.q || keys.e) touch();
        return { eye: flyPos, center: V.add(flyPos, front), front };
      }
      const eye = cam.mode === "fixed" ? cam.eye : [
        cam.target[0] + radius * Math.sin(yaw) * Math.cos(pitch),
        cam.target[1] + radius * Math.sin(pitch),
        cam.target[2] + radius * Math.cos(yaw) * Math.cos(pitch)];
      return { eye, center: cam.target, front: V.norm(V.sub(cam.target, eye)) };
    }

    // --- drawing
    function setState(st) {
      st = st || {};
      if (st.depth === false) gl.disable(gl.DEPTH_TEST); else gl.enable(gl.DEPTH_TEST);
      gl.depthFunc(gl.LEQUAL);
      if (st.cull && st.cull !== "none") {
        gl.enable(gl.CULL_FACE);
        gl.cullFace(st.cull === "front" ? gl.FRONT : gl.BACK);
      } else gl.disable(gl.CULL_FACE);
      return st.frontFace === "cw" ? gl.CW : gl.CCW;
    }

    function drawObjects(prog, objects, base, flip, lamps, frontFace) {
      /* Rendering upside down into a texture flips the winding, so flip the front face too. */
      gl.frontFace(flip < 0 ? (frontFace === gl.CCW ? gl.CW : gl.CCW) : frontFace);
      for (const o of objects) {
        if (o.lamp && !lamps) continue;
        const p = o.lamp ? lampProgram : prog;
        const vals = Object.assign({}, base, { model: o.model, normalMatrix: M.normalMatrix(o.model) }, o.uniforms);
        if (o.lamp) vals.color = o.lamp;
        gl.useProgram(p.program);
        gl.uniform1f(gl.getUniformLocation(p.program, "lm_flipY"), flip);
        gl.uniform1f(gl.getUniformLocation(p.program, "lm_height"), gl.drawingBufferHeight);
        /* o.textures maps a shader texture name to another loaded texture, e.g. a floor texture. */
        let tex = textures;
        if (o.textures) {
          tex = Object.assign({}, textures);
          for (const k in o.textures) tex[k] = textures[o.textures[k]];
        }
        applyUniforms(gl, p, vals, tex);
        const m = mesh(o.mesh);
        gl.bindVertexArray(m.vao);
        if (o.instances) gl.drawArraysInstanced(gl.TRIANGLES, 0, m.count, o.instances);
        else gl.drawArrays(gl.TRIANGLES, 0, m.count);
      }
    }

    function fullscreen(prog, base, flip) {
      gl.useProgram(prog.program);
      gl.uniform1f(gl.getUniformLocation(prog.program, "lm_flipY"), flip);
      gl.uniform1f(gl.getUniformLocation(prog.program, "lm_height"), gl.drawingBufferHeight);
      applyUniforms(gl, prog, base, textures);
      gl.bindVertexArray(emptyVao);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }

    let last = performance.now(), time = 0;
    function frame(now) {
      const dt = Math.min((now - last) / 1000, 0.1);
      last = now;
      if (!reduced && cfg.animate !== false) { time += dt; dirty = true; }
      const c = cameraState(dt);

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; dirty = true; sceneTarget = null; }
      if (!dirty || !program) return;
      dirty = false;

      const aspect = w / h;
      const fov = ((cfg.fov ? cfg.fov(state) : cam.fov) * Math.PI) / 180;
      const right = V.norm(V.cross(c.front, [0, 1, 0]));
      const base = {
        time, aspect, resolution: [w, h],
        view: M.lookAt(c.eye, c.center, [0, 1, 0]),
        projection: M.perspective(fov, aspect, 0.1, 100),
        model: M.ident(), normalMatrix: M.normalMatrix(M.ident()),
        viewPosition: c.eye, cameraFront: c.front, cameraRight: right, cameraUp: V.cross(right, c.front),
        tanHalfFov: Math.tan(fov / 2),
      };
      Object.assign(base, cfg.uniforms ? cfg.uniforms(state, time, base) : null);
      const objects = cfg.objects ? cfg.objects(state, time) : [];
      if (autoPending) {
        const known = new Set(Object.keys(base));
        for (const o of objects) for (const k in o.uniforms || {}) known.add(k);
        syncAutoControls(autoPending, known);
        autoPending = null;
      }
      Object.assign(base, autoValues);
      const st = cfg.state ? cfg.state(state) : {};

      if (cfg.sampler) {
        const s = cfg.sampler(state);
        const wrap = { repeat: gl.REPEAT, mirror: gl.MIRRORED_REPEAT, clamp: gl.CLAMP_TO_EDGE }[s.wrap || "repeat"];
        for (const t of imageTextures) {
          gl.bindTexture(gl.TEXTURE_2D, t);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, s.filter === "nearest" ? gl.NEAREST : gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, s.filter === "nearest" ? gl.NEAREST : gl.LINEAR_MIPMAP_LINEAR);
        }
      }

      if (cfg.shadow) {                                   // pass 1: depth from the light
        const sh = cfg.shadow(state, time);
        const s = sh.size || 6;
        base.lightViewProjection = M.mul(M.ortho(-s, s, -s, s, sh.near || 1, sh.far || 20), M.lookAt(sh.eye, sh.center || [0, 0, 0], [0, 1, 0]));
        gl.bindFramebuffer(gl.FRAMEBUFFER, shadowTarget.fb);
        gl.viewport(0, 0, shadowTarget.w, shadowTarget.h);
        gl.clear(gl.DEPTH_BUFFER_BIT);
        setState({});
        const bias = sh.bias || 0;
        if (bias) { gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(bias * 2, bias * 4); }
        drawObjects(depthProgram, objects, base, -1, false, gl.CCW);
        gl.disable(gl.POLYGON_OFFSET_FILL);
        textures.shadowMap = shadowTarget.depth;
      }

      const clear = cfg.clear ? cfg.clear(state) : [0.1, 0.1, 0.12];
      if (sceneProgram) {                                 // scene into a texture, then a full-screen pass
        if (!sceneTarget) sceneTarget = target(w, h, false);
        gl.bindFramebuffer(gl.FRAMEBUFFER, sceneTarget.fb);
        gl.viewport(0, 0, w, h);
        gl.clearColor(clear[0], clear[1], clear[2], 1);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        drawObjects(sceneProgram, objects, base, -1, true, setState(st));
        textures.scene = sceneTarget.color;
      }

      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, w, h);
      gl.clearColor(clear[0], clear[1], clear[2], 1);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      if (backProgram) { setState({ depth: false }); fullscreen(backProgram, base, 1); }
      if (cfg.fullscreen || sceneProgram) {
        setState({ depth: false });
        fullscreen(program, base, 1);
      } else {
        drawObjects(program, objects, base, 1, true, setState(st));
      }
    }

    let visible = false, raf = 0;
    const loop = (now) => { if (visible) { frame(now); raf = requestAnimationFrame(loop); } };
    new IntersectionObserver((entries) => {
      visible = entries[0].isIntersecting;
      cancelAnimationFrame(raf);
      if (visible) { last = performance.now(); dirty = true; raf = requestAnimationFrame(loop); }
    }, { rootMargin: "100px" }).observe(canvas);
  }

  function addCaption(el, cfg) {
    if (!cfg.caption) return;
    const p = document.createElement("p");
    p.className = "lm-caption";
    p.textContent = cfg.caption;
    el.appendChild(p);
  }

  LM.mountAll = function () { document.querySelectorAll("[data-demo]").forEach(mount); };
  /* Deferred scripts run before DOMContentLoaded, so demos.js has registered everything by then. */
  if (document.readyState === "complete") LM.mountAll();
  else document.addEventListener("DOMContentLoaded", LM.mountAll);
})();
