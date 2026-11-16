// Markdown repairs applied to model output before rendering.
//
// The model writes markdown that is *almost* right. Two failures show up in this
// app's chat history and neither is the parser's fault, so we patch the input
// instead of loosening the renderer.

const FENCE = /^ {0,3}(`{3,}|~{3,})/
const ALIGN_CELL = /^:?-+:?$/

// Split a table row on unescaped pipes only: models escape literal pipes inside
// cells as `\|`, and those must not count as cell separators.
function splitRow(line) {
	const cells = []
	let cell = ''
	for (let i = 0; i < line.length; i++) {
		const char = line[i]
		if (char === '\\' && i + 1 < line.length) {
			cell += char + line[i + 1]
			i++
			continue
		}
		if (char === '|') {
			cells.push(cell)
			cell = ''
			continue
		}
		cell += char
	}
	cells.push(cell)

	// The optional outer pipes are not cells.
	if (cells.length && cells[0].trim() === '') cells.shift()
	if (cells.length && cells[cells.length - 1].trim() === '') cells.pop()
	return cells
}

// A GFM table only exists when the delimiter row has exactly as many cells as the
// header row. Models routinely emit `|---|---|` under a 3-column header, and then the
// whole block renders as one paragraph of literal pipes. Evening the delimiter row
// out to the header's width is lossless: it only ever describes alignment.
export function repairTables(markdown) {
	if (!markdown?.includes('|')) return markdown

	const lines = markdown.split('\n')
	let fence = null

	for (let i = 1; i < lines.length; i++) {
		const line = lines[i]

		const fenceMatch = line.match(FENCE)
		if (fenceMatch) {
			const marker = fenceMatch[1][0]
			if (fence === null) fence = marker
			else if (fence === marker) fence = null
			continue
		}
		if (fence !== null) continue

		if (!line.includes('|')) continue
		const align = splitRow(line)
		if (!align.length || !align.every(cell => ALIGN_CELL.test(cell.trim()))) continue

		const headerLine = lines[i - 1]
		if (!headerLine.includes('|')) continue
		const header = splitRow(headerLine)
		if (!header.length || header.length === align.length) continue

		const cells = align.map(cell => cell.trim() || '---')
		while (cells.length < header.length) cells.push('---')
		lines[i] = `|${cells.slice(0, header.length).join('|')}|`
	}

	return lines.join('\n')
}

// `remarkMath` treats any two single dollars on one line as an inline formula, so
// "cheap: $0 to ~$20 per month, and $5 elsewhere" becomes one giant KaTeX span and
// the sentence is mangled. Real math in this app carries TeX syntax; a "formula"
// made of plain prose does not. Those get demoted back to text.
const TEX_SIGNAL = /(\\[a-zA-Z]+|[\^_{}])/
// Lowercase words only: single letters and `AB`-style products are math, `to` and
// `per` are not.
const PROSE_WORD = /[a-z]{2,}/
const PROSE_JUNK = /[`*#~→–—·]|\]\(|->|<\/?[a-z]/
// A formula does not end on a dangling binary operator; a swallowed price does
// ("$0.03 / $0.15" leaves the span "0.03 / ").
const DANGLING_TAIL = /[/+*,:(–—-]\s*$/

function looksLikeProse(value) {
	if (TEX_SIGNAL.test(value)) return false
	return PROSE_WORD.test(value) || PROSE_JUNK.test(value) || DANGLING_TAIL.test(value)
}

function demoteProseMath(node) {
	if (!Array.isArray(node.children)) return
	for (let i = 0; i < node.children.length; i++) {
		const child = node.children[i]
		if (child.type === 'inlineMath' && looksLikeProse(child.value)) {
			node.children[i] = { type: 'text', value: `$${child.value}$` }
			continue
		}
		demoteProseMath(child)
	}
}

// Must be used *after* `remarkMath`: plugins are parsers, so this transformer
// already sees the math nodes that `remarkMath` produced.
export function remarkGuardDollars() {
	return tree => demoteProseMath(tree)
}

export function prepareMarkdown(markdown) {
	return repairTables(markdown)
}
