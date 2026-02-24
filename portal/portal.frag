#version 330 core

in vec2 vUV;
out vec4 FragColor;

uniform float uTime;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

void main() {
    // uv: 0..1 -> p: -1..1
    vec2 p = vUV * 2.0 - 1.0;
    p.x *= 1.3333; // hơi bù aspect (ước lượng cho đẹp)

    float r = length(p);
    float a = atan(p.y, p.x);

    // swirl
    float swirl = sin(10.0 * r - 2.2 * uTime + 3.0 * a);

    // ring mask (vành cổng)
    float ringCenter = 0.55 + 0.03 * sin(uTime * 1.7);
    float ring = exp(-abs(r - ringCenter) * 18.0);

    // core glow
    float core = exp(-r * 6.0);

    // sparks/noise
    float n = hash21(p * 8.0 + uTime * 0.2);
    float sparks = smoothstep(0.92, 1.0, n) * ring;

    // color palette (cyan/purple neon)
    vec3 c1 = vec3(0.10, 0.85, 1.00);
    vec3 c2 = vec3(0.85, 0.15, 1.00);

    float t = 0.5 + 0.5 * swirl;
    vec3 col = mix(c2, c1, t);

    // combine
    float glow = ring * (0.9 + 0.6 * t) + 0.35 * core + 0.9 * sparks;

    // vignette
    float vig = smoothstep(1.2, 0.2, r);

    vec3 outCol = col * glow * vig;

    // alpha for additive blending
    FragColor = vec4(outCol, clamp(glow, 0.0, 1.0));
}
