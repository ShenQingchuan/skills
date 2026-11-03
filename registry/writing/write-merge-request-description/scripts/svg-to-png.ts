const [input, output] = Bun.argv.slice(2);
if (!input || !output) {
  throw new Error("Usage: bun svg-to-png.ts input.svg output.png");
}

const svg = await Bun.file(input).text();
const root = svg.match(/<svg\b[^>]*>/)?.[0];
const width = Number(root?.match(/\bwidth="(\d+)"/)?.[1]);
const height = Number(root?.match(/\bheight="(\d+)"/)?.[1]);
if (!width || !height) {
  throw new Error("SVG must have numeric width and height attributes");
}

await using view = new Bun.WebView({ width, height });
await view.navigate(Bun.pathToFileURL(input).href);
await view.evaluate("document.fonts.ready");
await Bun.write(output, await view.screenshot({ format: "png" }));
