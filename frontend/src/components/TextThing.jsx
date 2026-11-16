import { useEffect, useLayoutEffect, useRef, useState } from "react";
import ModelSelector from "./ModelSelector";
import Send from "../Assets/send.svg?react";
import Stop from "../Assets/stop.svg?react"
import Add from "../Assets/add.svg?react"
import Close from "../Assets/close.svg?react"
import { motion, useMotionValue, useSpring } from 'framer-motion'

const layoutSpring = { type: "spring", stiffness: 260, damping: 26 }

// One text-2xl line is 32px; anything past ~40px means the text has wrapped to a second line.
const WRAP_THRESHOLD = 40

// Matches max-h-64.
const MAX_TEXTAREA_HEIGHT = 256

export default function TextThing({ sendMessage, active, interrupt, expanded, model, setModel, models }) {


	const [larger, setLarger] = useState(false)
	const [value, setValue] = useState("")

	// The textarea height lives in React state instead of native `field-sizing-content`:
	// the browser grows the box between renders, so any measured target would be stale and
	// the card would snap instead of animating.
	const [textHeight, setTextHeight] = useState(32)
	const textRef = useRef(null)

	// The card is bottom-anchored, so its height is animated on a clip window around the
	// content: the card unrolls upwards and text keeps its natural size (no scale squashing).
	// A spring is driven from the measured content height instead of Framer's `animate`
	// prop, which would read the post-flip layout as its starting point and snap.
	const contentHeight = useMotionValue(0)
	const clipHeight = useSpring(contentHeight, layoutSpring)
	const measured = useRef(false)
	const contentRef = useRef(null)

	const inputRef = useRef(null)
	const [files, setFiles] = useState([]);

	function addFile(file) {
		let old_files = [...files]
		old_files.push(file)
		setFiles(old_files)
	}


	useEffect(() => {
		console.log("file has changed")
		console.log(files)
	}, [files])

	// Measure the content's natural height and follow it, whatever changes it (typing,
	// a file chip, the layout flip itself).
	useLayoutEffect(() => {
		const el = contentRef.current
		if (!el) return
		const update = () => {
			const height = el.getBoundingClientRect().height
			contentHeight.set(height)
			// First measurement seeds the spring so the card doesn't animate open on mount.
			if (!measured.current) {
				measured.current = true
				clipHeight.jump(height)
			}
		}
		update()
		const observer = new ResizeObserver(update)
		observer.observe(el)
		return () => observer.disconnect()
	}, [contentHeight, clipHeight])

	// Fit the textarea to its content, clamped to max-h-64. Height is reset to 0 for the read
	// (never painted) so scrollHeight reports the full content height, not the current box.
	function measureText() {
		const el = textRef.current
		if (!el) return
		const previous = el.style.height
		el.style.height = "0px"
		const next = Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)
		el.style.height = previous
		setTextHeight(old => (old === next ? old : next))
	}

	useLayoutEffect(measureText, [value, larger])

	// Wrapped line count also changes when the box gets narrower (window resize, sidebar,
	// the expand flip) — a width change, not a value change.
	useEffect(() => {
		const el = textRef.current
		if (!el) return
		let lastWidth = el.getBoundingClientRect().width
		const observer = new ResizeObserver(() => {
			const width = el.getBoundingClientRect().width
			if (Math.abs(width - lastWidth) < 1) return
			lastWidth = width
			measureText()
		})
		observer.observe(el)
		return () => observer.disconnect()
	}, [])

	function send(button) {
		if (!active) {
			const message = value
			if (message != "") {
				sendMessage(message, files)
				setValue("")
				setFiles([])
				setLarger(false)
			}
		} else {
			if (button) {
				interrupt()
			}
		}

	}

	function handleChange(e) {
		const next = e.target.value
		setValue(next)
		// Hysteresis: it expands as soon as the text wraps, but only collapses once emptied,
		// so a changing width can never loop between the two layouts.
		if (!larger) {
			if (e.target.scrollHeight > WRAP_THRESHOLD) setLarger(true)
		} else if (next.trim() === "") {
			setLarger(false)
		}
	}

	return (
		<div className="relative bottom-0  w-204 min-w-9/16 max-w-full ">

			<div className="bg-secondary flex-col border  border-accent w-full  py-4 px-4 shadow-accent/20 shadow flex z-1 rounded-2xl relative min-w-9/16  max-w-full -translate-y-4  [box-shadow:0_-6px_8px_-3px_rgba(0,0,0,0.2)]"
				onDragOver={e => e.preventDefault()}
				onDrop={e => {
					addFile(e.dataTransfer.files[0])
					e.preventDefault()
				}}>
				<input
					ref={inputRef}
					type="file"
					className="hidden"
					onChange={e => { addFile(e.target.files?.[0] ?? null) }}
				/>

				<motion.div
					style={{ height: clipHeight }}
					className="w-full overflow-hidden flex flex-col justify-end">

					<div ref={contentRef} className="w-full shrink-0 flex flex-col">
						<div className={`flex grow ${files.length > 0 ? 'h-12' : 'h-0'} transition-all overflow-hidden items-center `}>
							{files.map((e, i) => (
								<div key={i} className="flex border p-1 items-center rounded-md mx-1 ">
									<div className="h-9 w-max max-w-32  text-sm flex items-center truncate overflow-hidden  rounded-md">{e.name}</div>
									<Close className="cursor-pointer" onClick={() => {
										let old_arr = [...files]
										let index = old_arr.findIndex(f => f.name == e.name)
										old_arr.splice(index, 1)
										setFiles(old_arr)
									}} />
								</div>
							))}
						</div>

						{/* Same children in both modes — only their classes change, so the DOM node
						    (and therefore the typed text) survives the flip. */}
						<div className="flex flex-wrap items-end">
							<div className="flex-none flex">
								<Add className="h-12 aspect-square fill-text/80 hover:bg-hover cursor-pointer rounded-xl" onClick={() => {
									console.log("clicky click")
									inputRef.current?.click()
								}} />
							</div>

							<div className={`flex items-center min-h-12 ${larger ? "order-first w-full" : "grow min-w-0 w-min "}`}>
								<textarea
									autoFocus
									ref={textRef}
									value={value}
									onChange={handleChange}
									onKeyDown={e => {
										if (e.key == "Enter" && !e.shiftKey) {
											e.preventDefault()
											send()
										}
									}}
									style={{ height: textHeight }}
									className="w-full z-20 my-auto  text-text max-h-64 overflow-y-auto resize-none text-xl placeholder:truncate lg:text-2xl "
									placeholder="Slop anything" />
							</div>

							{/* Ending part */}
							<div className="ml-auto flex flex-none flex-row-reverse items-center">
								<div onClick={() => {
									send(true)
								}} className={`send-btn h-12 w-12   ${!active ? "bg-accent" : "bg-accent/50"}  z-10 cursor-pointer rounded-xl flex items-center justify-center p-3`}>
									{!active ? <Send className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none" />
										: <Stop className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none" />
									}
								</div>
								<ModelSelector expanded={expanded} model={model} setModel={setModel} models={models} />
							</div>
						</div>
					</div>
				</motion.div>

			</div>
		</div>
	)
}
