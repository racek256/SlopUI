import Search from "../Assets/search.svg?react"
import Close from "../Assets/close.svg?react"
import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ArrowUP from "../Assets/arrow_up.svg?react"
import ArrowDOWN from "../Assets/arrow_down.svg?react"

export default function ModelSelector({expanded, model, setModel, models}){
	const [display, setDisplay] = useState(false) 
	const [query, setQuery] = useState("")
	const triggerRef = useRef();



	
	useEffect(()=>{
		function handleClick(e){
			if(!triggerRef.current?.contains(e.target)){
				// clicked outside
				setDisplay(false)
				setQuery("")
			}
		}
		document.addEventListener("pointerdown", handleClick)

	})

	return(
		<div ref={triggerRef}
		className="flex z-10 text-text items-center model-selector justify-center px-2 text-lg py-1 cursor-pointer hover:bg-hover rounded-lg transition-all" onClick={()=>{setDisplay(!display)}}>
		<p className="flex select-none justify-center items-center">{model?.name ?? "model"} {display ? <ArrowUP className="h-full aspect-square"/> : <ArrowDOWN className="h-full"/>} </p>
			<AnimatePresence>
				{display &&
				<motion.div
					initial={{opacity:0, y:10}}
					animate={{opacity:1, y:0}}
					exit={{opacity:0, y:10}}
					transition={{duration:0.05}}

					 onClick={e=>{e.stopPropagation()}} className={`bg-secondary border-accent  overflow-hidden border rounded-xl  shadow-card shadow-accent/20  absolute model-selector-box w-64 sm:w-92 h-72  ${!expanded ? "sm:top-[anchor(bottom)]":"sm:bottom-[anchor(top)]"} bottom-[anchor(top)]  -translate-x-1/2  cursor-auto`} >

					<div  className="flex h-12 p-2 ">	
						<Search className="h-full w-12 fill-text"/>	
						<input  value={query}  className="grow h-full  text-xl" placeholder="Search" onKeyDown={e=>{
							console.log("shift:" + e.shiftKey)
							console.log("enter:" + (e.key =="Enter"))
							if(e.key == "Enter" && !e.shiftKey){
								console.log("entered")
								models.map(e=>{
									if (e.name.toLowerCase().includes(query)){
										setModel(e)
										setDisplay(false)
										setQuery("")
									}
								})
							}
						}}
						 onChange={e=>{
							setQuery(e.target.value)
						}}/>
						<Close className="h-full w-8 transition-all cursor-pointer fill-text hover:bg-[#b8c4ff] rounded-md" onClick={()=>{setDisplay(false)}}/>
					</div>
					<div className="px-2 h-full flex-col">	
						<div className="flex-col flex  overflow-y-scroll tinyscroll h-full">
						{models.map((e,i)=>{
							if (e.name.toLowerCase().includes(query)){	
								return(
								<div key={i} className="w-full cursor-pointer bg-background hover:bg-hover/50 text-xl hover:bg-[#b8c4ff]/40 text-text transition-all rounded-lg px-2 py-1 my-1" onClick={()=>{
									setModel(e)
									setDisplay(false)
									setQuery("")
								}}>{e.name}</div>)
							}
						})}
						</div>
					</div>


				</motion.div> 
				}
			</AnimatePresence>
		</div>
	)
}

