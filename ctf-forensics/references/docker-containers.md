# Docker and Container Forensics

Use when the challenge provides a Docker image/save archive, exported container filesystem, `/var/lib/docker` artifacts, container logs/config, or a containerized incident whose layer history/runtime state matters.

## First Classify the Evidence

- **image archive (`docker save`)**: manifest/config + ordered filesystem layers;
- **container export (`docker export`)**: merged filesystem only, little/no layer history;
- **live/stopped container**: inspect, logs, diff, processes, mounts and network state;
- **host data directory**: container configs, JSON logs, overlay2 layers, volumes, metadata.

This distinction determines what history can still be recovered.

## CTF Workflow

1. Hash/preserve supplied artifacts before extraction.
2. Inspect manifest/config/`docker inspect` data: command, entrypoint, env, user, mounts, capabilities, network/PID modes.
3. Reconstruct layer order and inspect additions/deletions/whiteouts.
4. Compare runtime filesystem with original image where possible.
5. Search volumes, `/tmp`, application directories, history/config layers and deleted layer content for flags/secrets.
6. Correlate logs/process/network artifacts only if the challenge depends on runtime behavior.

## Layer Analysis

`docker save` preserves layers. Extract `manifest.json`, follow the listed layer order, and inspect each `layer.tar`. A secret copied in one layer and deleted in a later layer may still exist in the earlier layer.

Tools such as `dive`, `container-diff`, `tar`, and direct JSON inspection help, but simple layer extraction is often sufficient for CTFs.

Watch for overlay/OCI whiteout entries (`.wh.*`) indicating deletions.

## Runtime / Host Artifacts

High-value metadata:

- environment variables;
- bind mounts and named volumes;
- privileged mode / added capabilities;
- host PID/network namespaces;
- Docker socket mounts;
- entrypoint/command;
- container JSON logs;
- `/var/lib/docker/containers/<id>/config.v2.json`;
- overlay2 upper/merged directories.

For CTFs, a writable host mount or Docker socket may be part of the challenge chain; for pure forensics, it explains how evidence moved between host/container.

## `docker diff`

If a container is available, `docker diff` quickly identifies added/changed/deleted paths. Prioritize unexpected executables/scripts, application config, shell histories, cron/SSH changes, and files in temporary locations.

## Image vs Runtime Secret Hunting

Search both:

- current merged filesystem;
- earlier layers;
- image config/history;
- environment variables;
- volume content;
- build artifacts and package caches.

A `RUN rm secret` in a later Dockerfile layer does not remove the bytes from an earlier layer.

## Common Failure Modes

- Using only `docker export` and losing layer history.
- Inspecting current merged filesystem and missing secrets deleted in later layers.
- Ignoring volumes because they are not part of the image.
- Treating vulnerability scanning as the forensic objective when the flag is in build/runtime artifacts.
- Modifying a live evidence container before capturing inspect/log/diff state.

## Provenance

Consolidated from the original `analyzing-docker-container-forensics` Apache-2.0 skill and existing `ctf-forensics/disk-and-memory.md` container notes. Original source remains on `archive/pre-restructure-20260823`.
