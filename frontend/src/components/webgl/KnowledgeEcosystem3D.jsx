import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

export default function KnowledgeEcosystem3D({ className = "" }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 550;
    const height = container.clientHeight || 500;

    // 1. Scene & Camera Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0.5, 14);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    const disposables = [];

    // Helper: Create Canvas Textures for Pinned Classroom Notes
    const createPinnedNoteTexture = (title, category, pinColor, markerHex, icon) => {
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 360;
      const ctx = canvas.getContext("2d");

      // Chalk / Sticky Note Paper Background
      ctx.fillStyle = "#ffffff";
      ctx.roundRect(12, 12, 488, 336, 24);
      ctx.fill();

      // Marker Border
      ctx.strokeStyle = markerHex;
      ctx.lineWidth = 6;
      ctx.roundRect(12, 12, 488, 336, 24);
      ctx.stroke();

      // 3D Pushpin Graphic at Top Center
      ctx.fillStyle = pinColor;
      ctx.beginPath();
      ctx.arc(256, 32, 16, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 4;
      ctx.stroke();

      // Highlighter Category Pill
      ctx.fillStyle = markerHex;
      ctx.roundRect(40, 70, 160, 36, 12);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 20px -apple-system, sans-serif";
      ctx.fillText(category.toUpperCase(), 55, 95);

      // Icon & Main Skill Title
      ctx.fillStyle = "#0f172a";
      ctx.font = "bold 44px -apple-system, sans-serif";
      ctx.fillText(`${icon} ${title}`, 40, 180);

      // Hand-drawn Annotation Line in Caveat style
      ctx.fillStyle = "#64748b";
      ctx.font = "italic 26px serif";
      ctx.fillText("✓ Pinned for Peer Swaps", 40, 240);

      // Marker Underline
      ctx.strokeStyle = markerHex;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(40, 255);
      ctx.lineTo(340, 255);
      ctx.stroke();

      // Bottom Status Indicator
      ctx.fillStyle = markerHex;
      ctx.font = "bold 20px -apple-system, sans-serif";
      ctx.fillText("● Live 1-on-1 Workspace", 40, 305);

      const texture = new THREE.CanvasTexture(canvas);
      texture.minFilter = THREE.LinearFilter;
      texture.generateMipmaps = false;
      return texture;
    };

    // 2. Real 3D Pinned Notes Data
    const pinnedSkills = [
      {
        title: "FastAPI",
        category: "Backend",
        pinColor: "#ef4444",
        markerHex: "#10b981",
        icon: "⚡",
        pos: [-3.8, 2.2, 0.8],
        rot: [0.05, 0.15, -0.06],
      },
      {
        title: "React 19",
        category: "Frontend",
        pinColor: "#3b82f6",
        markerHex: "#0284c7",
        icon: "⚛️",
        pos: [3.8, 2.3, -0.5],
        rot: [-0.05, -0.2, 0.05],
      },
      {
        title: "AI / RAG",
        category: "AI Mentor",
        pinColor: "#a855f7",
        markerHex: "#9333ea",
        icon: "🤖",
        pos: [0, 3.2, 0.5],
        rot: [0.1, 0, -0.02],
      },
      {
        title: "UI / UX",
        category: "Design",
        pinColor: "#f43f5e",
        markerHex: "#e11d48",
        icon: "🎨",
        pos: [-3.9, -1.8, 0.6],
        rot: [-0.05, 0.15, 0.04],
      },
      {
        title: "System Design",
        category: "Architecture",
        pinColor: "#f59e0b",
        markerHex: "#d97706",
        icon: "📐",
        pos: [3.8, -1.6, 0.9],
        rot: [0.05, -0.15, -0.04],
      },
      {
        title: "Docker / Cloud",
        category: "DevOps",
        pinColor: "#10b981",
        markerHex: "#2563eb",
        icon: "🐳",
        pos: [0, -2.6, -0.8],
        rot: [-0.1, 0, 0.03],
      },
    ];

    const noteGeo = new THREE.BoxGeometry(2.4, 1.6, 0.08);
    disposables.push(noteGeo);

    const noteMeshes = pinnedSkills.map((skill) => {
      const texture = createPinnedNoteTexture(
        skill.title,
        skill.category,
        skill.pinColor,
        skill.markerHex,
        skill.icon
      );
      disposables.push(texture);

      const faceMaterial = new THREE.MeshStandardMaterial({
        map: texture,
        roughness: 0.4,
        metalness: 0.1,
      });

      const sideMaterial = new THREE.MeshStandardMaterial({
        color: 0xe2e8f0,
        roughness: 0.5,
      });

      disposables.push(faceMaterial, sideMaterial);

      const materials = [
        sideMaterial, // right
        sideMaterial, // left
        sideMaterial, // top
        sideMaterial, // bottom
        faceMaterial, // front
        sideMaterial, // back
      ];

      const mesh = new THREE.Mesh(noteGeo, materials);
      mesh.position.set(...skill.pos);
      mesh.rotation.set(...skill.rot);
      mesh.userData = { ...skill, basePos: [...skill.pos], baseRot: [...skill.rot] };
      mainGroup.add(mesh);
      return mesh;
    });

    // 3. Central Glowing Skill Exchange Orb
    const orbGeo = new THREE.SphereGeometry(1.1, 32, 32);
    const orbMat = new THREE.MeshStandardMaterial({
      color: 0x4f46e5,
      emissive: 0x4338ca,
      emissiveIntensity: 0.7,
      roughness: 0.2,
      metalness: 0.3,
    });
    disposables.push(orbGeo, orbMat);
    const orbMesh = new THREE.Mesh(orbGeo, orbMat);
    mainGroup.add(orbMesh);

    // 4. Marker Energy Beams connecting notes
    const beamMat = new THREE.LineBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.45,
      linewidth: 2,
    });
    disposables.push(beamMat);

    const beamLines = noteMeshes.map((note) => {
      const geo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        note.position,
      ]);
      disposables.push(geo);
      const line = new THREE.Line(geo, beamMat);
      mainGroup.add(line);
      return { line, geo, note };
    });

    // 5. Floating Chalk Particle Dust
    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const chalkColors = [
      new THREE.Color(0x4f46e5),
      new THREE.Color(0x0284c7),
      new THREE.Color(0x10b981),
      new THREE.Color(0xf59e0b),
      new THREE.Color(0xf43f5e),
    ];

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 14;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 8;

      const col = chalkColors[Math.floor(Math.random() * chalkColors.length)];
      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }

    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    disposables.push(particleGeo);

    const particleMat = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
    });
    disposables.push(particleMat);

    const particles = new THREE.Points(particleGeo, particleMat);
    mainGroup.add(particles);

    // 6. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 10, 8);
    scene.add(dirLight);

    // 7. Mouse Physics & Interactive Drag
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let velocityX = 0;
    let velocityY = 0;

    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      targetX = x * 0.35;
      targetY = y * 0.25;

      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        velocityY = deltaX * 0.005;
        velocityX = deltaY * 0.005;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handleMouseDown = (e) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    window.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mouseup", handleMouseUp);

    // 8. Animation Loop
    let animationFrameId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth mouse follow & drag rotation
      mouseX += (targetX - mouseX) * 0.05;
      mouseY += (targetY - mouseY) * 0.05;

      mainGroup.rotation.y += velocityY;
      mainGroup.rotation.x += velocityX;
      velocityX *= 0.92;
      velocityY *= 0.92;

      mainGroup.rotation.y = THREE.MathUtils.lerp(mainGroup.rotation.y, mouseX, 0.05);
      mainGroup.rotation.x = THREE.MathUtils.lerp(mainGroup.rotation.x, mouseY * 0.5, 0.05);

      // Central Orb pulse
      const orbScale = 1 + Math.sin(elapsed * 2) * 0.05;
      orbMesh.scale.set(orbScale, orbScale, orbScale);

      // 3D Pinned Notes gentle sway physics
      noteMeshes.forEach((note, index) => {
        const base = note.userData.basePos;
        const baseRot = note.userData.baseRot;

        // Dynamic faster pendulum sway
        const swayOffset = Math.sin(elapsed * 2.8 + index * 1.1) * 0.12;
        const swayAngle = Math.sin(elapsed * 2.5 + index * 0.9) * 0.08;

        note.position.y = base[1] + swayOffset;
        note.rotation.z = baseRot[2] + swayAngle;

        // Update beam line positions
        const beam = beamLines[index];
        if (beam) {
          const points = [new THREE.Vector3(0, 0, 0), note.position];
          beam.geo.setFromPoints(points);
        }
      });

      // Floating dust particles slow drift
      particles.rotation.y = elapsed * 0.03;

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };

    window.addEventListener("resize", handleResize);

    // 10. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("resize", handleResize);

      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      disposables.forEach((d) => {
        if (d && d.dispose) d.dispose();
      });

      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className={`relative w-full h-[450px] sm:h-[520px] md:h-[580px] flex items-center justify-center cursor-grab active:cursor-grabbing select-none ${className}`}
      aria-label="3D Interactive Pinned Whiteboard Knowledge Graph"
    />
  );
}
