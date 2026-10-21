"""The GLSL programs (version 1.20, which every desktop driver and Mesa's software
renderer understand)."""

MODEL_VERTEX = """
#version 120
attribute vec3 aPos;
attribute vec3 aNormal;
attribute vec3 aColor;
attribute vec4 aBary;
attribute vec4 aFlags;
uniform mat4 uMVP;
uniform mat4 uView;
varying vec3 vWorld;
varying vec3 vView;
varying vec3 vNormal;
varying vec3 vColor;
varying vec3 vBary;
varying vec3 vFlags;
void main() {
    vWorld = aPos;
    vView = (uView * vec4(aPos, 1.0)).xyz;
    vNormal = mat3(uView) * aNormal;
    vColor = aColor;           // byte attributes arrive already scaled to 0..1
    vBary = aBary.xyz * 255.0;
    vFlags = aFlags.xyz * 255.0;
    gl_Position = uMVP * vec4(aPos, 1.0);
}
"""

MODEL_FRAGMENT = """
#version 120
uniform vec3 uBase;
uniform vec3 uEdgeColor;
uniform vec3 uBackColor;
uniform vec4 uSection;       // plane normal and offset: what lies beyond is cut away
uniform float uSectionOn;
uniform float uUseColors;
uniform float uSmooth;
uniform float uOrtho;
uniform float uMode;         // 0 solid, 1 solid + edges, 2 wireframe
uniform float uAllEdges;     // 1: every triangle edge, 0: only the flagged ones
uniform float uLine;         // line width in pixels
varying vec3 vWorld;
varying vec3 vView;
varying vec3 vNormal;
varying vec3 vColor;
varying vec3 vBary;
varying vec3 vFlags;

void main() {
    if (uSectionOn > 0.5 && dot(vWorld, uSection.xyz) > uSection.w) discard;

    // 0 on an edge, 1 away from it; only edges that count take part
    vec3 d = fwidth(vBary) * uLine;
    vec3 away = smoothstep(vec3(0.0), d, vBary);
    vec3 counted = mix(vec3(1.0), away, mix(vFlags, vec3(1.0), uAllEdges));
    float edge = 1.0 - min(counted.x, min(counted.y, counted.z));
    if (uMode > 1.5) {
        if (edge < 0.05) discard;
        gl_FragColor = vec4(uEdgeColor, 1.0);
        return;
    }

    vec3 n = uSmooth > 0.5 ? normalize(vNormal) : normalize(cross(dFdx(vView), dFdy(vView)));
    vec3 toEye = uOrtho > 0.5 ? vec3(0.0, 0.0, 1.0) : normalize(-vView);
    bool front = gl_FrontFacing;
    if (dot(n, toEye) < 0.0) n = -n;

    vec3 key = normalize(vec3(0.35, 0.55, 1.0));
    vec3 fill = normalize(vec3(-0.7, -0.25, 0.45));
    float hemi = 0.5 + 0.5 * n.y;
    float light = 0.30 + 0.20 * hemi + 0.58 * max(dot(n, key), 0.0) + 0.16 * max(dot(n, fill), 0.0);
    vec3 base = uUseColors > 0.5 ? vColor : uBase;
    vec3 colour = base * light;
    float shine = pow(max(dot(reflect(-key, n), toEye), 0.0), 40.0) * 0.20;
    colour += vec3(shine);
    if (uSectionOn > 0.5 && !front) colour = uBackColor * (0.55 + 0.45 * max(dot(n, key), 0.0));
    if (uMode > 0.5) colour = mix(colour, uEdgeColor, edge * 0.9);
    gl_FragColor = vec4(colour, 1.0);
}
"""

PICK_VERTEX = """
#version 120
attribute vec3 aPos;
attribute vec4 aId;
uniform mat4 uMVP;
varying vec3 vWorld;
varying vec4 vId;
void main() {
    vWorld = aPos;
    vId = aId;
    gl_Position = uMVP * vec4(aPos, 1.0);
}
"""

PICK_FRAGMENT = """
#version 120
uniform vec4 uSection;
uniform float uSectionOn;
varying vec3 vWorld;
varying vec4 vId;
void main() {
    if (uSectionOn > 0.5 && dot(vWorld, uSection.xyz) > uSection.w) discard;
    gl_FragColor = vId;
}
"""

LINE_VERTEX = """
#version 120
attribute vec3 aPos;
uniform mat4 uMVP;
void main() { gl_Position = uMVP * vec4(aPos, 1.0); }
"""

LINE_FRAGMENT = """
#version 120
uniform vec4 uColor;
void main() { gl_FragColor = uColor; }
"""
