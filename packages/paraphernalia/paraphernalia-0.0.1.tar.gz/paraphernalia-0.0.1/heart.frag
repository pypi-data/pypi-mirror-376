#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform float u_time;

vec3 prideRainbow(float t) {
    vec3 colors[6];
    colors[0] = vec3(1.0, 0.0, 0.0);   // Red
    colors[1] = vec3(1.0, 0.5, 0.0);   // Orange
    colors[2] = vec3(1.0, 1.0, 0.0);   // Yellow
    colors[3] = vec3(0.0, 1.0, 0.0);   // Green
    colors[4] = vec3(0.0, 0.0, 1.0);   // Blue
    colors[5] = vec3(0.7, 0.0, 1.0);   // Purple

    t = fract(t); // Ensure t is always between 0 and 1
    float index = floor(t * 6.0);
    float nextIndex = mod(index + 1.0, 6.0);
    float mixFactor = fract(t * 6.0);
    
    return mix(colors[int(index)], colors[int(nextIndex)], mixFactor);
}

float heart(vec2 uv) {
    uv = (uv - vec2(0.5)) * 2.0;
    float x = uv.x;
    float y = uv.y - pow(abs(x) * 0.67, 0.65) * 0.8;
    return length(vec2(x, y)) - 0.7;
}

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
}

vec2 random2(vec2 st) {
    st = vec2(dot(st,vec2(127.1,311.7)),
              dot(st,vec2(269.5,183.3)));
    return -1.0 + 2.0*fract(sin(st)*43758.5453123);
}

mat2 rotate2d(float angle) {
    return mat2(cos(angle), -sin(angle),
                sin(angle), cos(angle));
}

float star(vec2 uv, float flare) {
    float d = length(uv);
    float m = .05/d;
    
    float rays = max(0., 1.-abs(uv.x*uv.y*1000.));
    m += rays*flare;
    
    rays = max(0., 1.-abs(uv.x*uv.y*1000.));
    m += rays*.3*flare;
    
    m *= smoothstep(1., .2, d);
    return m;
}

float sparkle(vec2 uv, float sparkleSize, float density, float speed) {
    vec2 i_st = floor(uv * density);
    vec2 f_st = fract(uv * density);

    float m_dist = 1.;
    vec2 m_point;
    float m_glow = 0.;
    float m_angle = 0.;
    float m_fade = 0.;

    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x),float(y));
            vec2 point = random2(i_st + neighbor);
            
            float angle = u_time * speed + random(i_st + neighbor) * 6.28;
            point = 0.5 + 0.3 * vec2(cos(angle), sin(angle));
            
            vec2 diff = neighbor + point - f_st;
            float dist = length(diff);

            if (dist < m_dist) {
                m_dist = dist;
                m_point = point;
                m_angle = angle;
                
                // Random fade-in/fade-out effect
                float fadeSpeed = random(i_st + neighbor) * 2.0 + 0.5;
                m_fade = abs(sin(u_time * fadeSpeed));
            }
            
            float timeFactor = sin(u_time * speed * 2. + random(i_st + neighbor) * 6.28) * 0.5 + 0.5;
            m_glow += timeFactor / (dist * dist * 40.);
        }
    }

    vec2 uv_rot = rotate2d(m_angle) * (f_st - m_point);
    
    float s = star(uv_rot / sparkleSize, m_glow);
    float sparkle = smoothstep(0.4, 0.0, m_dist);
    
    return s * sparkle * m_fade;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    
    float h = heart(uv);
    
    // Pride rainbow gradient for the heart
    vec3 heartColor = prideRainbow(uv.y + mod(u_time * 0.1, 1.0));
    
    // Background with subtle pride colors
    vec3 bgColor = prideRainbow(mod((uv.x + uv.y) * 0.5 + u_time * 0.05, 1.0)) * 0.3;
    
    // Combine heart and background
    vec3 color = mix(bgColor, heartColor, smoothstep(0.01, -0.01, h));
    
    // Add spinning, twinkly star-like sparkles on top
    float sparkles = sparkle(uv, 0.1, 4.0, 0.5);  // Increased density for more sparkles
    vec3 sparkleColor = vec3(1.0);  // White sparkles
    color += sparkleColor * sparkles * 10.0;
    
    gl_FragColor = vec4(color, 1.0);
}
