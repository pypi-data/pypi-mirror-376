#import camera
#import clipping

@group(0) @binding(90) var<storage> u_vertices: array<f32>;
@group(0) @binding(91) var<storage> u_color: array<f32>;
@group(0) @binding(92) var<uniform> u_thickness: f32;
@group(0) @binding(93) var<storage> u_indices: array<u32>;

struct GeoEdgeInput
{
  @builtin(position) position: vec4<f32>,
  @location(0) p: vec3<f32>,
  @location(1) @interpolate(flat) index: u32,
};


@vertex
fn vertex_main(@builtin(vertex_index) vertId: u32,
               @builtin(instance_index) instanceId: u32) -> GeoEdgeInput
{
  let p1 = vec3f(u_vertices[instanceId * 6],
                 u_vertices[instanceId * 6 + 1],
                 u_vertices[instanceId * 6 + 2]);
  let p2 = vec3f(u_vertices[instanceId * 6 + 3],
                 u_vertices[instanceId * 6 + 4],
                 u_vertices[instanceId * 6 + 5]);

  // thick lines in screen space, 
  // see https://www.iquilezles.org/www/articles/thicklines/thicklines.htm
  var tp1 = cameraMapPoint(p1);
  var tp2 = cameraMapPoint(p2);
  var p: vec3<f32>;

  var sp1 = tp1.xy/tp1.w;
  var sp2 = tp2.xy/tp2.w;
  sp1.x *= u_camera.aspect;
  sp2.x *= u_camera.aspect;
  let v = normalize(sp2 - sp1);
  var thickness = u_thickness * 0.5;
#ifdef SELECT_PIPELINE
    thickness = 10*thickness;
#endif SELECT_PIPELINE
  var normal = vec2<f32>(-v.y, v.x) * thickness;
  normal.x = normal.x / u_camera.aspect;
  var pos : vec4<f32>;
  if(vertId == 0) {
    pos = tp1;
    p = p1;
    normal = -normal;
  }
  else if(vertId == 1) {
    pos = tp1;
    p = p1;
  }
  else if(vertId == 2) {
    pos = tp2;
    p = p2;
    normal = -normal;
  }
  else {
    p = p2;
    pos = tp2;
  }

  pos = vec4<f32>(pos.xy + normal*pos.w, pos.zw);
  
  return GeoEdgeInput(pos, p, u_indices[instanceId]);
}

@fragment
fn fragment_main(input: GeoEdgeInput) -> @location(0) vec4<f32> {
  checkClipping(input.p);
  if (u_color[input.index*4+3] == 0.0) {
    discard;
  }
  return vec4<f32>(u_color[input.index * 4],
                   u_color[input.index * 4 + 1],
                   u_color[input.index * 4 + 2],
                   u_color[input.index * 4 + 3]);
}

@fragment
fn fragmentQueryIndex(input: GeoEdgeInput) -> @location(0) vec4<u32> {
  checkClipping(input.p);
  if (u_color[input.index*4+3] == 0.0) {
    discard;
  }
  return vec4<u32>(@RENDER_OBJECT_ID@, bitcast<u32>(input.position.z), 1u, input.index);
}
