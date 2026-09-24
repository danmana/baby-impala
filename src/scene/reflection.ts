import * as THREE from 'three';

/**
 * Planar reflection for the wet ground (y = 0 plane), adapted from the
 * approach in three's Reflector: mirror the camera, clip with an oblique near
 * plane, render into a mip-mapped target so rough areas can sample blurrier.
 */
export class PlanarReflection {
  readonly target: THREE.WebGLRenderTarget;
  readonly textureMatrix = new THREE.Matrix4();
  private cam = new THREE.PerspectiveCamera();
  private plane = new THREE.Plane();
  private normal = new THREE.Vector3(0, 1, 0);
  private pos = new THREE.Vector3(0, 0.0, 0);
  private tmp = {
    view: new THREE.Vector3(), target: new THREE.Vector3(), look: new THREE.Vector3(0, 0, -1),
    rot: new THREE.Matrix4(), clip: new THREE.Vector4(), q: new THREE.Vector4(),
  };
  scale: number;

  constructor(scale: number) {
    this.scale = scale;
    this.target = new THREE.WebGLRenderTarget(4, 4, {
      type: THREE.HalfFloatType,
      generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter,
      magFilter: THREE.LinearFilter,
    });
  }

  setSize(w: number, h: number) {
    const s = Math.max(0.05, this.scale);
    this.target.setSize(Math.max(4, Math.round(w * s)), Math.max(4, Math.round(h * s)));
  }

  render(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera, hide: THREE.Object3D[]) {
    const t = this.tmp;
    const camPos = new THREE.Vector3().setFromMatrixPosition(camera.matrixWorld);
    t.view.subVectors(this.pos, camPos);
    if (t.view.dot(this.normal) > 0) return; // camera below the plane
    t.view.reflect(this.normal).negate().add(this.pos);

    t.rot.extractRotation(camera.matrixWorld);
    t.look.set(0, 0, -1).applyMatrix4(t.rot).add(camPos);
    t.target.subVectors(this.pos, t.look).reflect(this.normal).negate().add(this.pos);

    const vc = this.cam;
    vc.position.copy(t.view);
    vc.up.set(0, 1, 0).applyMatrix4(t.rot).reflect(this.normal);
    vc.lookAt(t.target);
    vc.far = camera.far;
    vc.near = camera.near;
    vc.fov = camera.fov;
    vc.aspect = camera.aspect;
    vc.updateMatrixWorld();
    vc.projectionMatrix.copy(camera.projectionMatrix);

    this.textureMatrix.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1);
    this.textureMatrix.multiply(vc.projectionMatrix).multiply(vc.matrixWorldInverse);

    // oblique near plane clipping (Lengyel)
    this.plane.setFromNormalAndCoplanarPoint(this.normal, this.pos).applyMatrix4(vc.matrixWorldInverse);
    t.clip.set(this.plane.normal.x, this.plane.normal.y, this.plane.normal.z, this.plane.constant);
    const p = vc.projectionMatrix;
    t.q.x = (Math.sign(t.clip.x) + p.elements[8]) / p.elements[0];
    t.q.y = (Math.sign(t.clip.y) + p.elements[9]) / p.elements[5];
    t.q.z = -1.0;
    t.q.w = (1.0 + p.elements[10]) / p.elements[14];
    t.clip.multiplyScalar(2.0 / t.clip.dot(t.q));
    p.elements[2] = t.clip.x;
    p.elements[6] = t.clip.y;
    p.elements[10] = t.clip.z + 1.0 - 0.0;
    p.elements[14] = t.clip.w;

    const vis = hide.map((o) => o.visible);
    hide.forEach((o) => (o.visible = false));
    const prevTarget = renderer.getRenderTarget();
    const prevShadow = renderer.shadowMap.autoUpdate;
    renderer.shadowMap.autoUpdate = false;
    renderer.setRenderTarget(this.target);
    renderer.state.buffers.depth.setMask(true);
    if (renderer.autoClear === false) renderer.clear();
    renderer.render(scene, vc);
    renderer.shadowMap.autoUpdate = prevShadow;
    renderer.setRenderTarget(prevTarget);
    hide.forEach((o, i) => (o.visible = vis[i]));
  }

  dispose() {
    this.target.dispose();
  }
}
