import sys, asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1280, "height": 640}, device_scale_factor=2)
        await pg.goto("file://" + sys.argv[1] + "#rec"); await pg.wait_for_function("window.FILM"); await pg.evaluate("FILM.ready()")
        await pg.evaluate("""() => { FILM.seek(0); const st = document.getElementById('stage'); st.style.cssText = 'width:100vw;height:100vh;aspect-ratio:auto';
          document.getElementById('k').innerHTML = ''; document.getElementById('prog').style.display = 'none'; document.getElementById('wipe').style.display = 'none';
          Object.assign(S, { water: .35, minute: 45, storm: 0, moves: 1, pack: 1, packAll: 1, spin: 0, trees: 0, design: 0, patch: 0, keepOnly: 0 }); Object.assign(cam, { x: 262, y: 262, zoom: 1.22, angle: -.46, pitch: .64 });
          const d = document.createElement('div'); d.className = 'beat'; d.style.cssText = 'visibility:visible;width:56cqw';
          d.innerHTML = '<span class="ln md" style="font-size:7.6cqw">Which ground</span><span class="ln md" style="font-size:7.6cqw">floods a <span class="mk" style="background-size:100% 86%;color:#fff">building?</span></span>'
            + '<p class="sm" style="font-size:2cqw;max-width:24em">Every 5 m square of a London street, raised and lowered by 5 cm in a flood simulation. <b>15,788 tests in 1,956 runs</b>, about 8x less compute.</p>'
            + '<p class="tag" style="font-size:1.15cqw">Southwark, London · pink circles: street changes that shared one simulation · arrows: ground that moves the water at a building</p>';
          document.getElementById('k').append(d); }""")
        await pg.wait_for_timeout(400); await pg.evaluate("size()"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=sys.argv[2], type="png"); await b.close()
asyncio.run(main())
