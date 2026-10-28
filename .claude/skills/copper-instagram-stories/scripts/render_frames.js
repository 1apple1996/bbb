// Render Story frames (.dc.html artboards from a Design canvas) to 1080x1920 PNGs.
// Usage: node render_frames.js <project-dir> <blobs-dir> <out-dir> <file-prefix>...
//   project-dir: folder holding the canvas's .dc.html files (e.g. .../project)
//   blobs-dir:   folder of uploaded images named <asset-id>.<ext> (from Artifact read of each asset id)
//   file-prefix: which artboards to render, e.g. "Wed-" or "Main" (matches the start of the file name)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [projectDir, blobsDir, outDir, ...prefixes] = process.argv.slice(2);
  if (!projectDir || !blobsDir || !outDir || prefixes.length === 0) {
    console.error('usage: node render_frames.js <project-dir> <blobs-dir> <out-dir> <file-prefix>...');
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });
  const blobs = Object.fromEntries(
    fs.readdirSync(blobsDir).map((f) => [path.parse(f).name, path.resolve(blobsDir, f)])
  );
  const files = fs.readdirSync(projectDir)
    .filter((f) => f.endsWith('.dc.html') && prefixes.some((p) => f.startsWith(p)))
    .sort();

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const f of files) {
    let html = fs.readFileSync(path.join(projectDir, f), 'utf8');
    // The canvas runtime isn't available locally; the markup renders as plain HTML.
    html = html.replace('<script src="./support.js"></script>', '');
    html = html.replace(/\/_blob\/([0-9a-f]{32})/g, (m, id) => {
      if (!blobs[id]) throw new Error(`${f}: missing image ${id} in ${blobsDir}`);
      return 'file://' + blobs[id];
    });
    const tmp = path.join(outDir, `.${f}.html`);
    fs.writeFileSync(tmp, html);
    await page.goto('file://' + path.resolve(tmp));
    await page.evaluate(() => document.fonts.ready);
    // Sticker guides (dashed boxes) only show placement; real stickers are added in the Instagram app.
    await page.evaluate(() => {
      for (const el of document.querySelectorAll('[style*="dashed"]')) el.style.visibility = 'hidden';
    });
    await page.waitForTimeout(300);
    const out = path.join(outDir, f.replace('.dc.html', '.png'));
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
    fs.unlinkSync(tmp);
    console.log(out);
  }
  await browser.close();
})();
