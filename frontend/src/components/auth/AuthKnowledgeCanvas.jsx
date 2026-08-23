import React, { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * SkillSwap Arena — Interactive 3D WebGL Knowledge Network Canvas (Phase 7)
 * 
 * Visualizes a dynamic 3D network of floating skill nodes, connected learner/mentor
 * pathways, and orbital particle dust that subtly responds to user mouse parallax.
 * Theme-aware (light/dark mode) and memory-safe with proper geometry/material disposal.
 */
export default function AuthKnowledgeCanvas({ isDarkMode = false }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Detect reduced motion preference
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 45;

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 2. Palette Selection based on theme
    const nodeColors = isDarkMode
      ? [0x6366f1, 0x8b5cf6, 0x06b6d4, 0xf59e0b, 0xec4899]
      : [0x4f46e5, 0x7c3aed, 0x0284c7, 0xd97706, 0xdb2777];

    const lineColor = isDarkMode ? 0x818cf8 : 0x6366f1;
    const particleColor = isDarkMode ? 0x93c5fd : 0x3b82f6;

    // 3. Create Floating Skill Nodes (Spheres)
    const isMobile = window.innerWidth < 768;
    const nodeCount = isMobile ? 16 : 28;
    const nodes = [];
    const nodeGroup = new THREE.Group();

    const sphereGeometry = new THREE.SphereGeometry(0.85, 16, 16);

    for (let i = 0; i < nodeCount; i++) {
      const color = nodeColors[i % nodeColors.length];
      const material = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: isDarkMode ? 0.85 : 0.7,
      });

      const mesh = new THREE.Mesh(sphereGeometry, material);

      // Distribute in a spherical/orbital cloud
      const radius = 12 + Math.random() * 22;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      mesh.position.x = radius * Math.sin(phi) * Math.cos(theta);
      mesh.position.y = radius * Math.sin(phi) * Math.sin(theta);
      mesh.position.z = radius * Math.cos(phi) * 0.6; // Slightly flatten Z

      // Store drift velocities
      mesh.userData = {
        originalPos: mesh.position.clone(),
        speedX: (Math.random() - 0.5) * 0.015,
        speedY: (Math.random() - 0.5) * 0.015,
        speedZ: (Math.random() - 0.5) * 0.01,
        orbitAngle: Math.random() * Math.PI * 2,
        orbitSpeed: (0.002 + Math.random() * 0.003) * (Math.random() > 0.5 ? 1 : -1),
        orbitRadius: radius,
      };

      nodes.push(mesh);
      nodeGroup.add(mesh);
    }
    scene.add(nodeGroup);

    // 4. Dynamic Connection Lines (Knowledge Pathways)
    const maxConnections = isMobile ? 24 : 45;
    const linePositions = new Float32Array(maxConnections * 2 * 3);
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));

    const lineMaterial = new THREE.LineBasicMaterial({
      color: lineColor,
      transparent: true,
      opacity: isDarkMode ? 0.22 : 0.15,
      blending: THREE.AdditiveBlending,
    });

    const linesMesh = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(linesMesh);

    // 5. Background Ambient Particle Field (Knowledge Dust)
    const particleCount = isMobile ? 60 : 140;
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 80;
      particlePositions[i + 1] = (Math.random() - 0.5) * 80;
      particlePositions[i + 2] = (Math.random() - 0.5) * 40;
    }

    particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));

    const particleMaterial = new THREE.PointsMaterial({
      color: particleColor,
      size: 1.2,
      transparent: true,
      opacity: isDarkMode ? 0.45 : 0.3,
      blending: THREE.AdditiveBlending,
    });

    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // 6. Mouse Parallax Interaction
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };

    const handleMouseMove = (e) => {
      const windowHalfX = window.innerWidth / 2;
      const windowHalfY = window.innerHeight / 2;
      mouse.targetX = (e.clientX - windowHalfX) * 0.0008;
      mouse.targetY = (e.clientY - windowHalfY) * 0.0008;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // 7. Resize Observer
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener("resize", handleResize);

    // 8. Animation Loop
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      if (!prefersReducedMotion) {
        const elapsedTime = clock.getElapsedTime();

        // Smooth camera parallax
        mouse.x += (mouse.targetX - mouse.x) * 0.05;
        mouse.y += (mouse.targetY - mouse.y) * 0.05;

        camera.position.x = mouse.x * 20;
        camera.position.y = -mouse.y * 20;
        camera.lookAt(scene.position);

        // Slow ambient rotation of node group
        nodeGroup.rotation.y = elapsedTime * 0.04;
        nodeGroup.rotation.x = Math.sin(elapsedTime * 0.02) * 0.05;

        // Animate individual nodes
        nodes.forEach((node) => {
          node.userData.orbitAngle += node.userData.orbitSpeed;
          node.position.x = Math.cos(node.userData.orbitAngle) * node.userData.orbitRadius;
          node.position.y = Math.sin(node.userData.orbitAngle) * node.userData.orbitRadius;
          node.position.z += Math.sin(elapsedTime + node.userData.orbitAngle) * 0.02;
        });

        // Update connection lines between close nodes
        let lineIdx = 0;
        const positions = lineGeometry.attributes.position.array;
        const maxDist = isMobile ? 12 : 15;

        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            if (lineIdx >= maxConnections * 6) break;

            const dist = nodes[i].position.distanceTo(nodes[j].position);
            if (dist < maxDist) {
              // Vertex 1
              positions[lineIdx++] = nodes[i].position.x;
              positions[lineIdx++] = nodes[i].position.y;
              positions[lineIdx++] = nodes[i].position.z;
              // Vertex 2
              positions[lineIdx++] = nodes[j].position.x;
              positions[lineIdx++] = nodes[j].position.y;
              positions[lineIdx++] = nodes[j].position.z;
            }
          }
        }

        // Fill remaining line vertices with 0
        while (lineIdx < maxConnections * 6) {
          positions[lineIdx++] = 0;
        }
        lineGeometry.attributes.position.needsUpdate = true;

        // Slow drift for background particles
        particles.rotation.y = elapsedTime * 0.015;
      }

      renderer.render(scene, camera);
    };

    animate();

    // 9. Clean Lifecycle & Resource Disposal
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);

      sphereGeometry.dispose();
      lineGeometry.dispose();
      particleGeometry.dispose();
      lineMaterial.dispose();
      particleMaterial.dispose();

      nodes.forEach((mesh) => {
        mesh.material.dispose();
      });

      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [isDarkMode]);

  return (
    <div
      ref={mountRef}
      className="absolute inset-0 pointer-events-none z-0 overflow-hidden opacity-60 dark:opacity-80 transition-opacity duration-500"
      aria-hidden="true"
    />
  );
}
