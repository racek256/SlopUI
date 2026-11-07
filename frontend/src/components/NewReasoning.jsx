import { useLayoutEffect } from "react"
import { useState, useEffect, useRef } from "react"
import Reasoning from '../Assets/brain.svg?react'
import Search from '../Assets/search.svg?react'
import Webfetch from '../Assets/webfetch.svg?react'
import { AnimatePresence, motion } from 'framer-motion' // or 'framer-motion'

/*
export default function NewReasoning({ message }) {
console.log("rendering message in reasoning")
console.log(message)

	return (
		<div className="max-w-xl">
		{message?.reason_chain?.map((e,i)=>{
			let last = Boolean(!message.reason_chain[i+1])
			if (e.type == "reason"){
				return(
					<ReasoningAction reasoning={e?.content} finished={!last} last={last}/>
				)
			}else{
				return(
					<Action name={e?.type} last={last} finished={!last}/>
				)
			}

			
		})}
		</div>
	)
}
*/

const WINDOW = 2
const EASE = [0.22, 1, 0.36, 1]

export default function NewReasoning({ message }) {
  const chain = message?.reason_chain ?? []
  if (message?.reason_chain && chain.length==0){
  	chain.unshift({type:"Waking up"});
  }
  const start = Math.max(0, chain.length - WINDOW)
  const visible = chain.map((e, i) => ({ e, i })).slice(start)

  return (
    <div className="max-w-xl">
      <AnimatePresence initial={false}>
        {visible.map(({ e, i }) => {
			e.icon = e.type
			if(e?.type?.includes("obscura") || e?.type?.includes("lightpanda") || e?.type?.includes("webfetch")){
				e.icon="browsing"
			}else if(e?.type?.includes("websearch")){
				e.icon="websearch"
			}else{
				e.icon="hovno"
			}
			
          const last = i === chain.length - 1
          return (
            // OUTER: owns the height animation → does the pushing
            <motion.div
              key={i}                    // ABSOLUTE index, must be stable
              className="overflow-hidden"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.35, ease: EASE }}
            >
              {/* INNER: owns the slide → doesn't squish the content */}
              <motion.div
                initial={{ y: 28, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -28, opacity: 0 }}
                transition={{ duration: 0.28, ease: EASE }}
              >
                {e.type === 'reason'
                  ? <ReasoningAction  reasoning={e?.content} finished={!last} last={last} />
                  : <Action  name={e?.type} last={last} finished={!last} icon={e.icon}/>}
              </motion.div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}




function Action({ name, finished, last, icon }) {
	return (
	<div>
		<div className="flex items-center rounded-xl hover:bg-button/20 p-1 cursor-pointer select-none transition-all">
			<Spinner reasoning="search" finished={finished} icon={icon} />
			<p className="pl-2 text-[22px]">{name}</p>
		</div>
		{!last &&
		<div className="px-1 h-6 flex-col flex overflow-hidden">
			 <Spacer />
		</div>}
	</div>
	)
}

function ReasoningAction({ reasoning, finished, last }) {
	/*
		const textRef = useRef(null)
	
		// Scroll to the bottom whenever new reasoning text arrives
		useLayoutEffect(() => {
			const el = textRef.current
			if (!el) return
			el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
		}, [reasoning])
	
	*/



	const textRef = useRef(null)
	const rafRef = useRef(null)
	const posRef = useRef(0)

	useLayoutEffect(() => {
		const el = textRef.current
		if (!el || rafRef.current) return // loop already running; it reads the latest target each frame

		posRef.current = el.scrollTop
		let last = performance.now()

		const tick = (now) => {
			const dt = Math.min(now - last, 50) // ms, clamped for tab-switch spikes
			last = now

			const target = el.scrollHeight - el.clientHeight
			const diff = target - posRef.current

			if (diff < 0.5) {
				posRef.current = target
				el.scrollTop = target
				rafRef.current = null
				return
			}

			// frame-rate independent exponential ease toward the target
			const k = 1 - Math.pow(0.002, dt / 1000)
			posRef.current += diff * k
			el.scrollTop = posRef.current
			rafRef.current = requestAnimationFrame(tick)
		}

		rafRef.current = requestAnimationFrame(tick)
	}, [reasoning])

	useEffect(() => () => {
		cancelAnimationFrame(rafRef.current)
		rafRef.current = null
	}, [])

	return (
		<div className="flex items-stretch rounded-xl hover:bg-button/20 p-1 cursor-pointer select-none transition-all">
			<div className="flex flex-col ">
				<Spinner icon="reasoning" finished={finished} />
				{!last && <Spacer />}
			</div>
			<div
				ref={textRef}
				className="pl-2 w-full max-h-[94px] overflow-hidden  text-[#888484] [mask-image:linear-gradient(to_bottom,transparent_0%,black_25%,black_75%,transparent_100%)]">
				<p className="text-[16px]">{reasoning}</p>
			</div>
		</div>
	)
}


const DOT = 6;      // w-1.5 = 6px
const MARGIN = 1;   // my-px = 1px top + 1px bottom
const SLOT = DOT + MARGIN * 2; // 8px per dot
const GAP = 4;      // minimum breathing room between dots

function Spacer() {
	const spacer = useRef(null) 
	const [count, setCount] = useState(3)

	useLayoutEffect(() => {
		const el = spacer.current;
		const update = () => {
			const h = el.getBoundingClientRect().height;
			setCount(Math.max(0, Math.floor((h + GAP) / (SLOT + GAP))))
		}
		update()
		const ro = new ResizeObserver(update);
		ro.observe(el);
		return () => ro.disconnect();

	})

	return (
		<div ref={spacer} className="flex-col mt-1  w-10.25 min-h-8 grow justify-between   flex items-center">
			{Array.from({ length: count }).map((_, i) => (
				<div className="w-1.5 aspect-square bg-[#9a3412] rounded-full my-px  blur-[1px]  " />
			))}

		</div>
	)
}


function Spinner({ finished, icon }) {
	return (
		<div className="relative">
			<div className={`w-10.25 aspect-square rounded-full flex items-center justify-center bg-[#9a3412] transition-all ${!finished && "animate-spin spinner"} blur-[1px] `}>
				<div className={`w-8.25 rounded-full aspect-square bg-secondary`} >
				</div>
			</div>
			{icon == "reasoning" ? <Reasoning className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8" /> : icon=="websearch"? <Search className="fill-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6" /> :  icon=="browsing" ? <Webfetch className="fill-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"/> : <div/> }

		</div>
	)
}
