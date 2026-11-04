import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const HELP = `Usage:
  boss node <skill>/scripts/render.mjs <input.mmd> [options]

Render Mermaid source as a standalone SVG with Pele.

Options:
  -o, --output <file>       Output SVG path (default: input path with .svg)
      --css <file>         Inject a Pele theme CSS file into the SVG
      --max-width <px>     Adapt the layout to an available width
      --font-family <css>  Font used to measure and draw labels
      --font-size <px>     Base font size (default: 16)
      --padding <px>       Space around the diagram
      --fixed              Keep the natural pixel size instead of responsive sizing
      --allow-external     Enable links and external images (disabled by default)
  -h, --help               Show this help
`;

function fail(message) {
  throw new Error(message);
}

function numberOption(value, name, { integer = false, minimum = 0 } = {}) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < minimum || (integer && !Number.isInteger(number))) {
    fail(`${name} expects a ${integer ? 'whole ' : ''}number >= ${minimum}; received: ${value}`);
  }
  return number;
}

function parseArgs(args) {
  const options = { allowExternal: false, fixed: false, help: false };
  let input;

  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    const value = () => {
      index += 1;
      if (index >= args.length) fail(`${argument} requires a value`);
      return args[index];
    };

    switch (argument) {
      case '-h':
      case '--help':
        options.help = true;
        break;
      case '-o':
      case '--output':
        options.output = value();
        break;
      case '--css':
        options.css = value();
        break;
      case '--max-width':
        options.maxWidth = numberOption(value(), argument, { minimum: 1 });
        break;
      case '--font-family':
        options.fontFamily = value();
        break;
      case '--font-size':
        options.fontSize = numberOption(value(), argument, { minimum: 1 });
        break;
      case '--padding':
        options.padding = numberOption(value(), argument);
        break;
      case '--fixed':
        options.fixed = true;
        break;
      case '--allow-external':
        options.allowExternal = true;
        break;
      default:
        if (argument.startsWith('-')) fail(`Unknown option: ${argument}`);
        if (input) fail(`Only one input file is allowed; unexpected: ${argument}`);
        input = argument;
    }
  }

  return { input, options };
}

function defaultOutput(input) {
  const extension = path.extname(input);
  return extension ? `${input.slice(0, -extension.length)}.svg` : `${input}.svg`;
}

function injectCss(svg, css) {
  if (/<\/style/i.test(css)) fail('The CSS file must not contain a closing </style> tag');
  if (!/<svg\b[^>]*>/i.test(svg)) fail('Pele returned an invalid SVG document');
  return svg.replace(/<svg\b[^>]*>/i, (root) => `${root}\n<style>\n${css}\n</style>`);
}

async function main() {
  const { input, options } = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(HELP);
    return;
  }
  if (!input) fail(`Missing input file.\n\n${HELP}`);

  const output = path.resolve(options.output ?? defaultOutput(input));
  if (path.resolve(input) === output) fail('Input and output paths must be different');

  let pele;
  try {
    pele = await import('pele');
  } catch (error) {
    if (error?.code !== 'ERR_MODULE_NOT_FOUND') throw error;
    fail('Missing Pele dependency. Run: boss npm ci --prefix "$HOME/.agents/skills/registry/writing/draw-with-pele"');
  }

  const source = await readFile(input, 'utf8');
  if (!source.trim()) fail('The input file is empty');

  const renderOptions = {
    idPrefix: 'pele',
    links: options.allowExternal,
    images: options.allowExternal,
    responsive: !options.fixed,
  };
  for (const key of ['maxWidth', 'fontFamily', 'fontSize', 'padding']) {
    if (options[key] !== undefined) renderOptions[key] = options[key];
  }

  let result;
  try {
    result = pele.render(source, renderOptions);
  } catch (error) {
    if (!(error instanceof pele.PeleError)) throw error;
    const location = error.line > 0 ? ` (line ${error.line}, column ${error.column})` : '';
    console.error(`Pele ${error.code} error${location}: ${error.message}`);
    if (error.snippet) console.error(error.snippet);
    process.exitCode = 1;
    return;
  }

  let svg = result.svg;
  if (options.css) {
    const css = await readFile(options.css, 'utf8');
    svg = injectCss(svg, css);
  }

  await mkdir(path.dirname(output), { recursive: true });
  await writeFile(output, svg, 'utf8');
  console.log(`${output}\n${result.type} · ${result.width} × ${result.height} px`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
