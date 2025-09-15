#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform float u_time;

float heart(vec2 uv) {
    // Adjust the position and scale of the heart
    uv = (uv - vec2(0.5)) * vec2(2.5, 2.5);
    
    // Create the heart shape using a mathematical formula
    float r = length(uv) * 0.75;
    float a = atan(uv.y, uv.x);
    
    float h = abs(a) / (3.14159 / 2.0) - 1.0;
    h = sqrt(abs(h)) * (0.5 + 0.5 * cos(u_time));
    
    float d = r - h;
    
    return 1.0 - smoothstep(0.0, 0.05, d);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    
    vec3 color = vec3(1.0, 0.0, 0.3); // Heart color (pink-red)
    
    float mask = heart(uv);
    
    gl_FragColor = vec4(color * mask, 1.0);
}
