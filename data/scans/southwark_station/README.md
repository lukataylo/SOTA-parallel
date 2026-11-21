# Southwark station scan (Sat 21 Nov 2026, evening)

Gaussian splat made by the human with Scaniverse. Source page: https://scaniverse.com/scan/yqkxnkirl2vkxxfn

- `gaussians.spz`: SPZ version 3, gzip-compressed, 184,894 Gaussians, spherical-harmonic degree 3, 12 fractional bits for position. After gunzip: 16-byte header, then per-point blocks in this order: positions (9 bytes, three 24-bit signed fixed-point values), alpha (1), colour (3), scale (3), rotation (4), harmonics (45).
- `preview.jpg`: the page's preview image.
- Tagged position: 51.50385875, -0.10438880, which is OSGB 531663.6 E, 180028.1 N, or row 270, column 298 of `shared/terrain_512.npz`. Open ground at 3.61 m, 8 m from receptor 204.
- Quality: night capture, blurred. Half the Gaussians are more than about 30 m from the centre and there is no clean ground plane. Not good enough for centimetre step heights. See `docs/IPHONE_APP.md`.
- Orientation and scale against the map have not been checked.
