import * as THREE from "https://esm.sh/three@0.175.0";
import { OrbitControls } from "https://esm.sh/three@0.175.0/examples/jsm/controls/OrbitControls.js";

document.addEventListener("DOMContentLoaded", () => {
  /* ===========================
     PRELOADER
  ============================ */
  const loadingOverlay = document.getElementById("loading-overlay");
  const preCanvas = document.getElementById("preloader-canvas");
  if (preCanvas) {
    const ctx = preCanvas.getContext("2d");
    const cx = preCanvas.width / 2;
    const cy = preCanvas.height / 2;
    const maxR = 80, circleCount = 5, dotCount = 24;
    let t = 0, lt = 0;
    const loop = (ts) => {
      if (!lt) lt = ts;
      const dt = ts - lt; lt = ts; t += dt * 0.001;
      ctx.clearRect(0,0,preCanvas.width,preCanvas.height);
      ctx.beginPath(); ctx.arc(cx,cy,3,0,Math.PI*2); ctx.fillStyle="rgba(102,230,255,.9)"; ctx.fill();
      for (let c=0;c<circleCount;c++){
        const phase = (t*0.35 + c/circleCount) % 1;
        const r = phase*maxR; const o = 1 - phase;
        ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2);
        ctx.strokeStyle = `rgba(102,230,255,${o*0.18})`; ctx.lineWidth = 1; ctx.stroke();
        for (let i=0;i<dotCount;i++){
          const a = (i/dotCount)*Math.PI*2;
          const x = cx + Math.cos(a)*r; const y = cy + Math.sin(a)*r;
          const size = 2 * (1 - phase*0.5);
          ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y);
          ctx.strokeStyle = `rgba(102,230,255,${o*0.08})`; ctx.stroke();
          ctx.beginPath(); ctx.arc(x,y,size,0,Math.PI*2);
          ctx.fillStyle = `rgba(102,230,255,${o*.9})`; ctx.fill();
        }
      }
      if (loadingOverlay.style.display !== "none") requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
  const hidePreloader = () => {
    if (!loadingOverlay || loadingOverlay.style.display === "none") return;
    loadingOverlay.style.opacity = 0;
    setTimeout(() => (loadingOverlay.style.display = "none"), 500);
  };
  window.addEventListener("load", () => setTimeout(hidePreloader, 300));
  setTimeout(hidePreloader, 4000); // failsafe

  /* ===========================
     HUD CLOCK
  ============================ */
  const timestamp = document.getElementById("timestamp");
  const updateClock = () => {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    const ss = String(now.getSeconds()).padStart(2, "0");
    if (timestamp) timestamp.textContent = `TIME: ${hh}:${mm}:${ss}`;
  };
  updateClock(); setInterval(updateClock, 1000);

  /* ===========================
     NOTIFY BANNER
  ============================ */
  const note = document.getElementById("notification");
  let noteTimer=null;
  function notify(msg, type="warn", timeout=3000){
    if (!note) return;
    note.textContent = msg;
    note.dataset.type = type;
    note.classList.add("show");
    clearTimeout(noteTimer);
    noteTimer = setTimeout(()=> note.classList.remove("show"), timeout);
  }

  /* ===========================
     AUDIO + LOCAL VAD (visuals)
  ============================ */
  let audioContext = null, analyser = null;
  let audioData = null, freqData = null;
  let micSource = null, micActive = false;
  let audioSensitivity = 0.9, audioReactivity = 1.0;

  const vadState = {
    speaking: false,
    noiseFloor: 0.015,
    speakHold: 1.0,
    silenceHold: 0,
    attackFrames: 3,
    releaseFrames: 100, // ~1s at ~60fps
    thresholdRatio: 8.0,
    zcrWeight: 0.4
  };

  function initAudio() {
    if (audioContext) return;
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.85;
      audioData = new Float32Array(analyser.fftSize);
      freqData = new Uint8Array(analyser.frequencyBinCount);
      notify("AUDIO ANALYZER READY • TAP THE ORB TO ENABLE MIC", "ok", 2200);
    } catch (e) {
      console.error(e);
      notify("AUDIO INIT ERROR", "error", 4000);
    }
  }

  function vadTick() {
    if (!analyser || !audioData) return false;
    analyser.getFloatTimeDomainData(audioData);

    // RMS
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) sum += audioData[i] * audioData[i];
    const rms = Math.sqrt(sum / audioData.length);

    // ZCR
    let zc = 0, prev = audioData[0];
    for (let i = 1; i < audioData.length; i++) {
      const curr = audioData[i];
      if ((prev >= 0 && curr < 0) || (prev < 0 && curr >= 0)) zc++;
      prev = curr;
    }
    const zcr = zc / audioData.length;

    if (!vadState.speaking) {
      vadState.noiseFloor = 0.97 * vadState.noiseFloor + 0.03 * Math.min(rms, 0.05);
    }

    const ratio = rms / Math.max(1e-6, vadState.noiseFloor);
    const score = ratio + vadState.zcrWeight * zcr;

    let speakingDecision = vadState.speaking;
    if (!vadState.speaking) {
      if (score > vadState.thresholdRatio) {
        vadState.speakHold++;
        if (vadState.speakHold >= vadState.attackFrames) {
          speakingDecision = true;
          vadState.speakHold = 0;
        }
      } else {
        vadState.speakHold = 0;
      }
      vadState.silenceHold = 0;
    } else {
      if (score < vadState.thresholdRatio * 0.6) {
        vadState.silenceHold++;
        if (vadState.silenceHold >= vadState.releaseFrames) {
          speakingDecision = false;
          vadState.silenceHold = 0;
        }
      } else {
        vadState.silenceHold = 0;
      }
      vadState.speakHold = 0;
    }

    const changed = speakingDecision !== vadState.speaking;
    vadState.speaking = speakingDecision;

    return changed ? (speakingDecision ? "start" : "end") : false;
  }

  /* ===========================
     TINY WAVEFORM (defensive)
  ============================ */
  const wfCanvas = document.getElementById("waveform-canvas");
  const wfCtx = wfCanvas ? wfCanvas.getContext("2d") : null;
  function resizeWF(){
    if (!wfCanvas || !wfCtx) return;
    wfCanvas.width = wfCanvas.offsetWidth * devicePixelRatio;
    wfCanvas.height = wfCanvas.offsetHeight * devicePixelRatio;
    wfCtx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  }
  resizeWF(); window.addEventListener("resize", resizeWF);

  (function drawWF(){
    if (wfCanvas && wfCtx){
      const w = wfCanvas.width / devicePixelRatio;
      const h = wfCanvas.height / devicePixelRatio;
      wfCtx.clearRect(0,0,w,h);
      wfCtx.fillStyle = "rgba(0,0,0,.22)"; wfCtx.fillRect(0,0,w,h);
      wfCtx.beginPath(); wfCtx.strokeStyle = "rgba(102,230,255,.9)"; wfCtx.lineWidth = 2;
      const slice = w / (audioData ? audioData.length : 120);
      let x = 0;
      if (audioData && analyser) {
        analyser.getFloatTimeDomainData(audioData);
        for (let i=0;i<audioData.length;i++){
          const v = (audioData[i] * 0.5 + 0.5);
          const y = v * h;
          i===0 ? wfCtx.moveTo(x,y) : wfCtx.lineTo(x,y);
          x += slice;
        }
      } else {
        const t = performance.now()*0.001;
        for (let i=0;i<120;i++){
          const v = Math.sin(i*0.25 + t) * 0.2 + Math.sin(i*0.05 + t*1.7)*0.1;
          const y = h*0.5 + v*h*0.4;
          i===0 ? wfCtx.moveTo(x,y) : wfCtx.lineTo(x,y);
          x += slice;
        }
      }
      wfCtx.stroke();
    }
    requestAnimationFrame(drawWF);
  })();

  /* ===========================
     CIRCULAR VIS + RING
  ============================ */
  const circCanvas = document.getElementById("circular-canvas");
  const circCtx = circCanvas.getContext("2d");
  function resizeCirc(){
    circCanvas.width = circCanvas.offsetWidth;
    circCanvas.height = circCanvas.offsetHeight;
  }
  resizeCirc(); window.addEventListener("resize", resizeCirc);

  function drawCircular(){
    if (!analyser) return;
    const w = circCanvas.width, h = circCanvas.height;
    const cx = w/2, cy = h/2;
    analyser.getByteFrequencyData(freqData);
    circCtx.clearRect(0,0,w,h);
    const baseR = Math.min(w,h)*0.38; const rings = 3; const points = 180;
    for (let r=0;r<rings;r++){
      const ringR = baseR * (0.72 + r*0.16);
      const op = 0.85 - r*0.23;
      circCtx.beginPath();
      for (let i=0;i<points;i++){
        const segStart = Math.floor((r * analyser.frequencyBinCount)/(rings*1.5));
        const segEnd = Math.floor(((r+1) * analyser.frequencyBinCount)/(rings*1.5));
        const seg = Math.max(1, Math.floor((segEnd-segStart)/points));
        let sum = 0;
        const span = Math.max(1, segEnd - segStart);
        for (let j=0;j<seg;j++){
          const idx = segStart + ((i*seg + j) % span);
          sum += freqData[idx] || 0;
        }
        const v = (sum / (seg*255)) * (audioSensitivity/5) * audioReactivity;
        const dynR = ringR * (1 + v*0.5);
        const a = (i/points)*Math.PI*2;
        const x = cx + Math.cos(a)*dynR, y = cy + Math.sin(a)*dynR;
        i===0 ? circCtx.moveTo(x,y) : circCtx.lineTo(x,y);
      }
      circCtx.closePath();
      const grad = circCtx.createRadialGradient(cx,cy, ringR*0.75, cx,cy, ringR*1.25);
      grad.addColorStop(0, `rgba(102,230,255,${op})`);
      grad.addColorStop(1, `rgba(47,179,255,${op*.7})`);
      circCtx.strokeStyle = grad; circCtx.lineWidth = 2 + (rings-r);
      circCtx.shadowBlur = 14; circCtx.shadowColor = "rgba(102,230,255,.7)";
      circCtx.stroke();
    }
    circCtx.shadowBlur = 0;
  }

  const audioWave = document.getElementById("audio-wave");
  function updateRing(){
    if (!analyser || !audioData) return;
    analyser.getFloatTimeDomainData(audioData);
    let sum=0; for (let i=0;i<audioData.length;i++) sum += Math.abs(audioData[i]);
    const avg = sum / audioData.length;
    const f = 1 + avg * audioReactivity * (audioSensitivity/5) * 1.4;
    audioWave.style.transform = `translate(-50%,-50%) scale(${f.toFixed(3)})`;
    audioWave.style.borderColor = `rgba(102,230,255,${0.10 + avg*0.35})`;
  }

  /* ===========================
     THREE.JS ORB + STARS
  ============================ */
  let scene, camera, renderer, controls;
  let orbGroup, updateOrbUniforms, updateBackground;
  let clock = new THREE.Clock();
  let rotationSpeed = 1.0, distortionAmount = 1.0, resolution = 32;

  function initThree(){
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x031018, 0.045);

    camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.1, 1000);
    camera.position.set(0,0,10);

    renderer = new THREE.WebGLRenderer({ antialias:true, alpha:true, powerPreference:"high-performance" });
    renderer.setSize(innerWidth, innerHeight);
    renderer.setPixelRatio(devicePixelRatio);
    renderer.setClearColor(0x000000, 0);
    document.getElementById("three-container").appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.enableZoom = false;

    scene.add(new THREE.AmbientLight(0x88aabb, 1.2));
    const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(3,2,2); scene.add(dl);
    const p1 = new THREE.PointLight(0x66e6ff, 1.1, 10); p1.position.set(2,2,2); scene.add(p1);
    const p2 = new THREE.PointLight(0x2fb3ff, 1.0, 10); p2.position.set(-2,-2,-2); scene.add(p2);

    updateOrbUniforms = createOrb();
    updateBackground = createStars();

    window.addEventListener("resize", onResize);
    animate();
  }

  function onResize(){
    camera.aspect = innerWidth/innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
    resizeWF(); resizeCirc();
  }

  function createStars(){
    const g = new THREE.BufferGeometry();
    const count = 2800;
    const pos = new Float32Array(count*3);
    const col = new Float32Array(count*3);
    const c1 = new THREE.Color(0x66e6ff), c2 = new THREE.Color(0x2fb3ff), c3 = new THREE.Color(0x8de6ff);
    for (let i=0;i<count;i++){
      pos[i*3] = (Math.random()-0.5)*110;
      pos[i*3+1] = (Math.random()-0.5)*110;
      pos[i*3+2] = (Math.random()-0.5)*110;
      const pick = Math.random(); const c = pick<.34?c1:pick<.67?c2:c3;
      col[i*3]=c.r; col[i*3+1]=c.g; col[i*3+2]=c.b;
    }
    g.setAttribute("position", new THREE.BufferAttribute(pos,3));
    g.setAttribute("color", new THREE.BufferAttribute(col,3));
    const m = new THREE.ShaderMaterial({
      uniforms:{ time:{value:0} },
      vertexShader:`
        varying vec3 vColor; uniform float time;
        void main(){
          vColor = color;
          vec3 p = position;
          p.x += sin(time*0.1 + position.z*0.2)*0.06;
          p.y += cos(time*0.1 + position.x*0.2)*0.06;
          vec4 mv = modelViewMatrix * vec4(p,1.0);
          gl_PointSize = 0.9 * (300.0 / -mv.z);
          gl_Position = projectionMatrix * mv;
        }`,
      fragmentShader:`
        varying vec3 vColor;
        void main(){
          float r = distance(gl_PointCoord, vec2(0.5));
          if (r > 0.5) discard;
          float glow = pow(1.0 - r*2.0, 2.0);
          gl_FragColor = vec4(vColor, glow);
        }`,
      transparent:true, depthWrite:false, blending:THREE.AdditiveBlending, vertexColors:true
    });
    const pts = new THREE.Points(g,m); scene.add(pts);
    return (time)=>{ m.uniforms.time.value = time; };
  }

  function createOrb(){
    if (orbGroup) scene.remove(orbGroup);
    orbGroup = new THREE.Group();

    const radius = 2;
    const geo = new THREE.IcosahedronGeometry(radius, Math.max(1, Math.floor(resolution/8)));
    const mat = new THREE.ShaderMaterial({
      uniforms:{
        time:{value:0}, color:{value:new THREE.Color(0x66e6ff)},
        audioLevel:{value:0}, distortion:{value:distortionAmount}
      },
      vertexShader:`
        uniform float time, audioLevel, distortion;
        varying vec3 vN; varying vec3 vP;
        vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
        vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
        vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
        vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}
        float snoise(vec3 v){
          const vec2 C=vec2(1.0/6.0,1.0/3.0);
          const vec4 D=vec4(0.0,0.5,1.0,2.0);
          vec3 i=floor(v+dot(v,C.yyy));
          vec3 x0=v-i+dot(i,C.xxx);
          vec3 g=step(x0.yzx,x0.xyz);
          vec3 l=1.0-g;
          vec3 i1=min(g.xyz,l.zxy);
          vec3 i2=max(g.xyz,l.zxy);
          vec3 x1=x0-i1+C.xxx;
          vec3 x2=x0-i2+C.yyy;
          vec3 x3=x0-D.yyy;
          i=mod289(i);
          vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
          float n_=0.142857142857;
          vec3 ns=n_*D.wyz-D.xzx;
          vec4 j=p-49.0*floor(p*ns.z*ns.z);
          vec4 x_=floor(j*ns.z);
          vec4 y_=floor(j-7.0*x_);
          vec4 x=x_*ns.x+ns.yyyy;
          vec4 y=y_*ns.x+ns.yyyy;
          vec4 h=1.0-abs(x)-abs(y);
          vec4 b0=vec4(x.xy,y.xy);
          vec4 b1=vec4(x.zw,y.zw);
          vec4 s0=floor(b0)*2.0+1.0;
          vec4 s1=floor(b1)*2.0+1.0;
          vec4 sh=-step(h,vec4(0.0));
          vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
          vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
          vec3 p0=vec3(a0.xy,h.x);
          vec3 p1=vec3(a1.zw,h.y);
          vec3 p2=vec3(a1.xy,h.z);
          vec3 p3=vec3(a1.zw,h.w);
          vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
          p0*=norm.x; p1*=norm.y; p2*=norm.z; p3*=norm.w;
          vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);
          m*=m;
          return 42.0*dot(m*m, vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
        }
        void main(){
          vN = normalize(normalMatrix * normal);
          float slow = time*0.3;
          vec3 p = position;
          float n = snoise(vec3(position*0.55 + slow));
          p += normal * n * 0.22 * distortion * (1.0 + audioLevel);
          vP = p;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.0);
        }`,
      fragmentShader:`
        uniform float time; uniform vec3 color; uniform float audioLevel;
        varying vec3 vN; varying vec3 vP;
        void main(){
          vec3 viewDir = normalize(cameraPosition - vP);
          float fres = 1.0 - max(0.0, dot(viewDir, normalize(vN)));
          fres = pow(fres, 2.2 + audioLevel*2.5);
          float pulse = 0.7 + 0.3*sin(time*2.0);
          vec3 col = color * fres * pulse * (1.0 + audioLevel*0.8);
          float a = fres * (0.75 - audioLevel*0.3);
          gl_FragColor = vec4(col, a);
        }`,
      wireframe:true, transparent:true
    });
    const mesh = new THREE.Mesh(geo, mat);
    orbGroup.add(mesh);

    const glowGeo = new THREE.SphereGeometry(radius*1.18, 32, 32);
    const glowMat = new THREE.ShaderMaterial({
      uniforms:{ time:{value:0}, color:{value:new THREE.Color(0x66e6ff)}, audioLevel:{value:0} },
      vertexShader:`varying vec3 vN; varying vec3 vP; uniform float audioLevel;
        void main(){ vN=normalize(normalMatrix*normal); vP=position*(1.0+audioLevel*0.22);
          gl_Position=projectionMatrix*modelViewMatrix*vec4(vP,1.0); }`,
      fragmentShader:`varying vec3 vN; varying vec3 vP; uniform vec3 color; uniform float time; uniform float audioLevel;
        void main(){ vec3 viewDir=normalize(cameraPosition - vP);
          float fres=1.0-max(0.0,dot(viewDir,normalize(vN))); fres=pow(fres, 3.0 + audioLevel*3.0);
          float pulse=0.55 + 0.45*sin(time*2.0);
          float af = 1.0 + audioLevel*3.0;
          vec3 col = color * fres * (0.8 + 0.2*pulse) * af;
          float a = fres * (0.28 * af) * (1.0 - audioLevel*0.2);
          gl_FragColor = vec4(col, a);
        }`,
      transparent:true, side:THREE.BackSide, blending:THREE.AdditiveBlending, depthWrite:false
    });
    orbGroup.add(new THREE.Mesh(glowGeo, glowMat));

    scene.add(orbGroup);
    return (time, level)=>{
      mat.uniforms.time.value = time;
      mat.uniforms.audioLevel.value = level;
      mat.uniforms.distortion.value = distortionAmount;
      glowMat.uniforms.time.value = time;
      glowMat.uniforms.audioLevel.value = level;
    };
  }

  function disturbOrb() {
    if (!orbGroup) return;
    const base = distortionAmount;
    distortionAmount = base + 0.6;
    setTimeout(()=>{ distortionAmount = base; }, 140);
    const ox = orbGroup.rotation.x, oy = orbGroup.rotation.y;
    gsap.fromTo(orbGroup.rotation, { x: ox+0.15, y: oy-0.25 }, { x: ox, y: oy, duration: 0.35, ease: "power3.out" });
    gsap.fromTo(camera.position, { z: 9.2 }, { z: 10, duration: 0.45, ease: "power2.out" });
    notify("VOICE DETECTED", "ok", 900);
  }

  /* ===========================
     DOM PARTICLES
  ============================ */
  const domParticles = [];
  function initDOMParticles(){
    const holder = document.getElementById("floating-particles");
    holder.innerHTML = ""; domParticles.length = 0;
    const count = 800, w=innerWidth, h=innerHeight, cx=w/2, cy=h/2;
    for (let i=0;i<count;i++){
      const el = document.createElement("div");
      el.style.position="absolute"; el.style.width="2px"; el.style.height="2px"; el.style.borderRadius="50%";
      el.style.backgroundColor = `rgba(102,230,255,${Math.random()*0.5+0.15})`;
      const ang = Math.random()*Math.PI*2;
      const minD = 180, maxD = Math.max(w,h)*0.8;
      const d = minD + Math.sqrt(Math.random()) * (maxD-minD);
      const x = Math.cos(ang)*d + cx; const y = Math.sin(ang)*d + cy;
      el.style.left = x+"px"; el.style.top = y+"px";
      holder.appendChild(el);
      domParticles.push({
        el, x, y, speed: Math.random()*0.5+0.1,
        ang: Math.random()*Math.PI*2, angSp: (Math.random()-0.5)*0.02,
        amp: Math.random()*46+18, sz:1.6, pSp: Math.random()*0.04+0.01, pPh: Math.random()*Math.PI*2
      });
    }
    (function anim(){
      const cx=innerWidth/2, cy=innerHeight/2;
      for (const p of domParticles){
        p.ang += p.angSp;
        const ox = cx + Math.cos(p.ang)*p.amp;
        const oy = cy + Math.sin(p.ang)*p.amp;
        const t = performance.now()*0.001;
        const nx = Math.sin(t*p.speed + p.ang)*4;
        const ny = Math.cos(t*p.speed + p.ang*0.7)*4;
        const X = ox + nx, Y = oy + ny;
        p.el.style.left = X+"px"; p.el.style.top = Y+"px";
        const pulse = 1 + Math.sin(t*p.pSp + p.pPh)*0.35;
        const s = p.sz * pulse; p.el.style.width = s+"px"; p.el.style.height = s+"px";
        p.el.style.opacity = Math.min(.85, .25 + Math.sin(t*p.pSp + p.pPh)*.15 + .35);
      }
      requestAnimationFrame(anim);
    })();
  }

  /* ===========================
     REALTIME (ASR + streamed TTS)
  ============================ */

  // Safer base detection (localhost / file:// dev)
  const API_BASE = (() => {
    const isLocalHost =
      location.hostname === "localhost" ||
      location.hostname === "127.0.0.1" ||
      location.hostname === "::1" ||
      location.protocol === "file:";
    if (isLocalHost) return "http://127.0.0.1:8000";
    return ""; // same-origin in prod
  })();

  // Token endpoint (your server returns ephemeral token)
  //const TOKEN_ENDPOINT = `${API_BASE}/rt-token`;
  const IS_LOCAL = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.protocol === "file:";
  const TOKEN_ENDPOINT = IS_LOCAL ? "http://127.0.0.1:8000/rt-token" : "/api/rt-token";


  const transcriptEl = document.getElementById("transcript-stream");

  // WebSocket + mic buffering
  let ws = null;
  let wsOpen = false;

  let captureNode = null;
  let appendedMsSinceCommit = 0;
  let everAppended = false;
  let lastCommitAt = 0;

  // ---- Assistant captions (text) ----
  function appendAssistantText(delta){
    if (!delta) return;
    let frag = transcriptEl.querySelector(".assistant.frag");
    if (!frag) {
      frag = document.createElement("span");
      frag.className = "assistant frag";
      transcriptEl.appendChild(frag);
    }
    frag.textContent += delta;
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }
  function endAssistantCaption(){
    const frag = transcriptEl.querySelector(".assistant.frag");
    if (!frag) return;
    const line = document.createElement("div");
    line.className = "final assistant";
    line.textContent = frag.textContent.trim();
    frag.remove();
    if (line.textContent) transcriptEl.appendChild(line);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }

  // ---- User transcript UI ----
  function appendTranscript(deltaText) {
    if (!deltaText) return;
    let frag = transcriptEl.querySelector(".frag.user");
    if (!frag) {
      frag = document.createElement("span");
      frag.className = "frag user";
      transcriptEl.appendChild(frag);
    }
    frag.textContent += deltaText;
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }
  async function finalizeTranscript(fullText) {
    const frag = transcriptEl.querySelector(".frag.user");
    const line = document.createElement("div");
    line.className = "final user";
    line.textContent = (fullText || (frag ? frag.textContent : "") || "").trim();
    if (frag) frag.remove();
    if (line.textContent) transcriptEl.appendChild(line);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }

  /* ---------- PCM Player (interruptible + resampling) ---------- */
  class PCMPlayer {
    constructor() {
      // Browsers often force 48000 regardless of what you ask for
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.sampleRate = this.ctx.sampleRate; // actual device rate (often 48000)
      this.serverRate = this.sampleRate;     // will be updated from config/events
      this.node = null;
      this.started = false;
      this.activeGen = 0; // gate for late chunks
    }
    async init() {
      if (this.node) return;
      const workletCode = `
        class PCMFeeder extends AudioWorkletProcessor {
          constructor() {
            super();
            this.buffers = [];
            this.readIndex = 0;
            this.cur = null;
            this.port.onmessage = e => {
              const d = e.data || {};
              if (d.type === 'push') {
                this.buffers.push(new Float32Array(d.payload));
              } else if (d.type === 'clear') {
                this.buffers.length = 0;
                this.cur = null;
                this.readIndex = 0;
              }
            };
          }
          process(_inputs, outputs) {
            const out = outputs[0][0];
            let i = 0;
            while (i < out.length) {
              if (!this.cur || this.readIndex >= this.cur.length) {
                this.cur = this.buffers.shift();
                this.readIndex = 0;
                if (!this.cur) {
                  while (i < out.length) out[i++] = 0;
                  return true;
                }
              }
              const take = Math.min(out.length - i, this.cur.length - this.readIndex);
              out.set(this.cur.subarray(this.readIndex, this.readIndex + take), i);
              i += take;
              this.readIndex += take;
            }
            return true;
          }
        }
        registerProcessor('pcm-feeder', PCMFeeder);
      `;
      const blob = new Blob([workletCode], { type: "application/javascript" });
      const url = URL.createObjectURL(blob);
      await this.ctx.audioWorklet.addModule(url);
      this.node = new AudioWorkletNode(this.ctx, 'pcm-feeder');
      this.node.connect(this.ctx.destination);
    }
    async start() {
      await this.init();
      if (this.ctx.state === "suspended") await this.ctx.resume();
      this.started = true;
    }
    clear() {
      if (!this.node) return;
      this.node.port.postMessage({ type: 'clear' });
    }
    setGeneration(gen) {
      this.activeGen = gen;
    }
    setServerRate(hz) {
      this.serverRate = hz || this.sampleRate;
    }
    static resampleLinear(f32, from, to) {
      if (!f32 || from === to) return f32;
      const len = Math.max(1, Math.round(f32.length * to / from));
      const out = new Float32Array(len);
      const ratio = (f32.length - 1) / (len - 1);
      for (let i = 0; i < len; i++) {
        const x = i * ratio;
        const i0 = Math.floor(x);
        const i1 = Math.min(f32.length - 1, i0 + 1);
        const t = x - i0;
        out[i] = f32[i0] * (1 - t) + f32[i1] * t;
      }
      return out;
    }
    enqueueBase64PCM16(b64, gen) {
      if (!this.started || !b64) return;
      if (gen !== this.activeGen) return;

      const raw = atob(b64);
      const len = raw.length;
      const buf = new ArrayBuffer(len);
      const view = new Uint8Array(buf);
      for (let i = 0; i < len; i++) view[i] = raw.charCodeAt(i);
      const i16 = new Int16Array(buf);
      let f32 = new Float32Array(i16.length);
      for (let i = 0; i < i16.length; i++) f32[i] = Math.max(-1, Math.min(1, i16[i] / 32768));

      if (this.serverRate !== this.sampleRate) {
        f32 = PCMPlayer.resampleLinear(f32, this.serverRate, this.sampleRate);
      }
      this.node.port.postMessage({ type: 'push', payload: f32.buffer }, [f32.buffer]);
    }
  }
  let pcmPlayer = null;

  // generation for dropping stale audio/text
  let responseGen = 0;
  let activeGen = 0;
  function bumpGeneration() {
    activeGen = ++responseGen;
    if (pcmPlayer) pcmPlayer.setGeneration(activeGen);
  }
  function hardStopAssistantAudio(reason="barge-in") {
    try { if (wsOpen) ws.send(JSON.stringify({ type: "response.cancel" })); } catch {}
    if (pcmPlayer) pcmPlayer.clear();
    notify("TTS INTERRUPTED", "warn", 900);
  }

  // ---- helpers: resample + PCM16 + base64 for mic → WS ----
  function downsampleTo16k(buffer, inRate) {
    const outRate = 16000;
    if (inRate === outRate) return buffer;
    const ratio = inRate / outRate;
    const newLen = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLen);
    let idx = 0, pos = 0;
    while (idx < newLen) {
      const nextPos = Math.round((idx + 1) * ratio);
      let sum = 0, count = 0;
      for (let i = Math.floor(pos); i < Math.min(buffer.length, nextPos); i++) {
        sum += buffer[i]; count++;
      }
      result[idx++] = count ? (sum / count) : 0;
      pos = nextPos;
    }
    return result;
  }
  function float32ToPCM16LE(float32) {
    const out = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return out;
  }
  function abToBase64(ab) {
    const bytes = new Uint8Array(ab);
    let bin = "";
    const CHUNK = 0x8000;
    for (let i = 0; i < bytes.length; i += CHUNK) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
    }
    return btoa(bin);
  }

  // --------- Realtime start ---------
  async function startRealtime(userMediaStream) {
    try {
      // 1) fetch ephemeral token
      const r = await fetch(TOKEN_ENDPOINT, { cache: "no-store" });
      if (!r.ok) {
        const body = await r.text().catch(() => "");
        notify(`AUTH HTTP ERROR (${r.status})`, "error", 5000);
        console.error("rt-token error:", r.status, body);
        return;
      }
      const tok = await r.json();
      const token = tok?.client_secret?.value || tok?.client_secret || tok?.value;
      if (!token) {
        notify("AUTH MISSING TOKEN", "error", 5000);
        console.error("rt-token response:", tok);
        return;
      }

      // 2) connect WS to Realtime
      const url = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview";
      const tryOpen = (protocols) =>
        new Promise((resolve, reject) => {
          const sock = new WebSocket(url, protocols);
          let opened = false;
          sock.onopen = () => { opened = true; resolve(sock); };
          sock.onerror = (e) => { if (!opened) reject(e); };
          sock.onclose = (ev) => {
            if (!opened) reject(new Error(`WS close before open. code=${ev.code} reason=${ev.reason || "(no reason)"}`));
          };
        });

      const protoA = ["realtime", "openai-beta.realtime-v1", `openai-insecure-api-key.${token}`];
      const protoB = ["realtime", `openai-insecure-api-key.${token}`, "openai-beta.realtime-v1"];

      let sock;
      try {
        sock = await tryOpen(protoA);
      } catch (e1) {
        console.warn("WS open failed (A). Retrying with alt protocol order…", e1);
        sock = await tryOpen(protoB);
      }

      ws = sock;
      wsOpen = true;
      everAppended = false;
      appendedMsSinceCommit = 0;
      lastCommitAt = performance.now();
      notify("REALTIME LINK ESTABLISHED", "ok", 1800);

      // pick output sample-rate to match the actual device rate
      const desiredOutRate = 24000;
        (pcmPlayer && pcmPlayer.sampleRate) ? pcmPlayer.sampleRate : 24000;
      if (pcmPlayer) pcmPlayer.setServerRate(desiredOutRate);

      // 3) session config (ASR + audio out)
      ws.send(JSON.stringify({
        type: "session.update",
        session: {
          // mic input (we send 16k PCM)
          input_audio_format: "pcm16",
          input_audio_sample_rate_hz: 16000,
          input_audio_channels: 1,
          input_audio_transcription: { model: "gpt-4o-mini-transcribe" },
          input_audio_noise_reduction: { type: "near_field" },

          // assistant audio out
          output_audio_format: "pcm16",
          output_audio_sample_rate_hz: desiredOutRate,
          voice: "verse", // try "alloy" if you want brighter

          // end-of-turn detection
          turn_detection: {
            type: "server_vad",
            threshold: 0.1,
            prefix_padding_ms: 300,
            silence_duration_ms: 1000
          },

          // tone
          instructions: "You are Jarvis. Be concise, helpful, and speak in short, friendly, energetic sentences."
        }
      }));

      // 4) begin mic streaming
      startMicPCMStream(userMediaStream);

      // 5) message handling
      ws.onmessage = (ev) => {
        let msg;
        try { msg = JSON.parse(ev.data); } catch { return; }
        const t = msg.type;

        // Live ASR text
        if (t === "conversation.item.input_audio_transcription.delta") {
          appendTranscript(msg.delta || "");
          return;
        }
        if (t === "conversation.item.input_audio_transcription.completed") {
          finalizeTranscript(msg.transcript || "");
          return;
        }

        // When speech stops, request a response (text + audio)
        if (t === "transcription.speech_stopped" || t === "input_audio_buffer.collected") {
          ws.send(JSON.stringify({
            type: "response.create",
            response: {
              modalities: ["text","audio"],
              audio: { format: "pcm16", sample_rate_hz: desiredOutRate, voice: "verse" }
            }
          }));
          return;
        }

        // New response lifecycle
        if (t === "response.created") {
          bumpGeneration();           // new gen for this response
          if (pcmPlayer) pcmPlayer.clear(); // clear residual audio
          return;
        }

        // If API surfaces the actual sample rate, capture it
        if (t === "response.output_audio.start" || t === "response.audio.start") {
          if (msg?.sample_rate_hz && pcmPlayer) {
            pcmPlayer.setServerRate(msg.sample_rate_hz);
          }
          return;
        }

        // Assistant text deltas for captions
        if (t === "response.output_text.delta" || t === "response.transcript.delta") {
          appendAssistantText(msg.delta || msg.text || msg.value || "");
          return;
        }
        if (t === "response.completed" || t === "response.output_text.done") {
          endAssistantCaption();
          return;
        }

        // Assistant audio deltas (base64 PCM16)
        if (t === "response.output_audio.delta" || t === "response.audio.delta") {
          const b64 = msg.delta || msg.audio;
          if (b64 && pcmPlayer) pcmPlayer.enqueueBase64PCM16(b64, activeGen);
          return;
        }
        if (t === "response.output_audio.done") {
          return;
        }

        // Barge-in: user starts talking → cancel assistant
        if (t === "input_audio_buffer.speech_started") {
          hardStopAssistantAudio("server-vad");
          return;
        }

        if (t === "error") {
          console.error("Realtime error:", msg);
          notify(`REALTIME ERROR: ${msg.error?.message || "unknown"}`, "error", 5000);
        }
      };

      ws.onclose = (ev) => {
        wsOpen = false;
        everAppended = false;
        appendedMsSinceCommit = 0;
        stopMicPCMStream();
        const reason = ev.reason || "(no reason)";
        if ([1008, 4401, 4403].includes(ev.code)) {
          notify(`REALTIME AUTH FAILED (${ev.code})`, "error", 6000);
        } else {
          notify(`REALTIME CLOSED (${ev.code})`, "warn", 3000);
        }
        console.warn("WS closed:", ev.code, reason);
      };

      ws.onerror = (e) => {
        console.error("WS onerror:", e);
        notify("REALTIME SOCKET ERROR", "error", 4000);
      };
    } catch (e) {
      console.error("startRealtime fatal:", e);
      notify("REALTIME INIT FAILED", "error", 6000);
    }
  }

  // mic capture → 16k PCM16 → WS append
  function startMicPCMStream(userMediaStream) {
    if (!audioContext) return;
    const inputNode = audioContext.createMediaStreamSource(userMediaStream);

    captureNode = audioContext.createScriptProcessor(4096, 1, 1);
    const sink = audioContext.createGain(); sink.gain.value = 0;
    captureNode.connect(sink); sink.connect(audioContext.destination);
    inputNode.connect(captureNode);

    const inRate = audioContext.sampleRate;           // ~48000
    const frameMs = 220;                              // ≥100ms per append
    const samplesPerFrame = Math.floor(inRate * (frameMs / 1000));

    let acc = new Float32Array(0);

    captureNode.onaudioprocess = (e) => {
      if (!wsOpen || !ws || ws.readyState !== 1) return;

      const input = e.inputBuffer.getChannelData(0);
      const tmp = new Float32Array(acc.length + input.length);
      tmp.set(acc, 0); tmp.set(input, acc.length);
      acc = tmp;

      while (acc.length >= samplesPerFrame) {
        const chunk = acc.subarray(0, samplesPerFrame);
        const rest  = acc.subarray(samplesPerFrame);
        acc = new Float32Array(rest.length); acc.set(rest, 0);

        const ds    = downsampleTo16k(chunk, inRate);   // -> 16k
        const pcm16 = float32ToPCM16LE(ds);
        const b64   = abToBase64(pcm16.buffer);

        try {
          ws.send(JSON.stringify({ type: "input_audio_buffer.append", audio: b64 }));
          everAppended = true;
          appendedMsSinceCommit += (ds.length / 16000) * 1000; // samples → ms
        } catch {}
      }
    };
  }
  function stopMicPCMStream() {
    if (captureNode) {
      try { captureNode.disconnect(); } catch {}
      captureNode = null;
    }
  }

  // Encourage server finalize after local silence / throttle commits
  function maybeCommitToServer(force = false) {
    if (!wsOpen || !ws || ws.readyState !== 1) return;
    if (!everAppended) return;

    const now = performance.now();
    if (!force) {
      if (appendedMsSinceCommit < 120) return;
      if (now - lastCommitAt < 300) return;
    }
    try {
      ws.send(JSON.stringify({ type: "input_audio_buffer.commit" }));
      lastCommitAt = now;
      appendedMsSinceCommit = 0;
    } catch {}
  }

  /* ===========================
     ANIMATE LOOP
  ============================ */
  let lastVADEmit = 0;
  let silenceFrames = 0;
  function animate(){
    requestAnimationFrame(animate);
    controls && controls.update();
    const t = clock.getElapsedTime();

    let level = 0;
    if (analyser && freqData){
      analyser.getByteFrequencyData(freqData);
      let sum=0; for (let i=0;i<freqData.length;i++) sum += freqData[i];
      level = ((sum / freqData.length) / 255) * (audioSensitivity/5);
      drawCircular(); updateRing();
    }

    // Local VAD barge-in / finalize
    if (micActive) {
      const change = vadTick();
      if (change === "start") {
        hardStopAssistantAudio("local-vad");
        const now = performance.now();
        if (now - lastVADEmit > 120) {
          disturbOrb();
          lastVADEmit = now;
        }
        silenceFrames = 0;
      } else if (vadState.speaking) {
        silenceFrames = 0;
      } else {
        silenceFrames++;
        if (silenceFrames > 30) { // ~500ms @60fps
          maybeCommitToServer();
          silenceFrames = 0;
        }
      }
    }

    updateOrbUniforms && updateOrbUniforms(t, level);
    updateBackground && updateBackground(t);
    if (orbGroup){
      const rotF = 1 + level * audioReactivity;
      orbGroup.rotation.y += 0.005 * rotationSpeed * rotF;
      orbGroup.rotation.z += 0.002 * rotationSpeed * rotF;
    }
    renderer.render(scene, camera);
  }

  /* ===========================
     BOOT
  ============================ */
  initAudio();
  initThree();
  initDOMParticles();
  notify("SYSTEM ONLINE • TAP THE ORB TO ENABLE MIC", "ok", 2800);

  // One-time mic+realtime enable on user gesture
  async function enableMicAndRealtime() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
        }
      });
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioContext.state === "suspended") await audioContext.resume();

      // init realtime auwsdio player
      if (!pcmPlayer) {
        pcmPlayer = new PCMPlayer();
        await pcmPlayer.start(); // must be after user gesture
      }

      micSource = audioContext.createMediaStreamSource(stream);
      if (analyser) micSource.connect(analyser);
      micActive = true;

      startRealtime(stream);

      notify("MIC CONNECTED • REALTIME ON", "ok", 1600);
    } catch (err) {
      console.error("getUserMedia error:", err);
      notify("MIC PERMISSION DENIED", "error", 4000);
    }
  }
// Activate mic on any user gesture (mouse/touch/pen/keyboard)
let micArmed = false;

const armMic = async (ev) => {
  if (micArmed) return;
  micArmed = true;
  ev?.preventDefault?.();   // helps iOS treat it as a real gesture
  await enableMicAndRealtime();
};

// Pointer covers mouse, touch, pen on modern browsers
window.addEventListener("pointerdown", armMic, { once: true, passive: false });

// Fallbacks for older mobile/Safari
window.addEventListener("touchend", armMic, { once: true, passive: false });
window.addEventListener("click", armMic, { once: true });

// Optional: keyboard access (Space/Enter)
window.addEventListener("keydown", (e) => {
  if (!micArmed && (e.key === " " || e.key === "Enter")) armMic(e);
}, { once: true });

});
