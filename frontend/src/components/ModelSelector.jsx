import Search from "../Assets/search.svg?react"
import Close from "../Assets/close.svg?react"
import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ArrowUP from "../Assets/arrow_up.svg?react"
import ArrowDOWN from "../Assets/arrow_down.svg?react"
export default function ModelSelector(expanded){
	const [display, setDisplay] = useState(false) 
	const triggerRef = useRef();

	useEffect(()=>{
		function handleClick(e){
			if(!triggerRef.current?.contains(e.target)){
				// clicked outside
				setDisplay(false)
			}
		}
		document.addEventListener("pointerdown", handleClick)

	})

	return(
		<div ref={triggerRef}
		className="flex items-center model-selector justify-center px-2 text-lg py-1 cursor-pointer hover:bg-[#eae7e6] rounded-lg transition-all" onClick={()=>{setDisplay(!display)}}>
		<p className="flex select-none justify-center items-center">model {display ? <ArrowUP className="h-full aspect-square"/> : <ArrowDOWN className="h-full"/>} </p>
			<AnimatePresence>
				{display &&
				<motion.div
					initial={{opacity:0, y:10}}
					animate={{opacity:1, y:0}}
					exit={{opacity:0, y:10}}

					 onClick={e=>{e.stopPropagation()}} className={`bg-[#fcf9f8] border-[#b8c4ff] border rounded-xl  shadow-card shadow-[#b8c4ff]/20  absolute model-selector-box w-92 h-72  ${!expanded ? "top-[anchor(bottom)]":"bottom-[anchor(top)]"} -translate-x-1/2  cursor-auto`} >

					<div  className="flex h-12 p-2">	
						<Search className="h-full w-12"/>	
						<input autoFocus className="grow h-full  text-xl" placeholder="Search"/>
						<Close className="h-full w-8 transition-all cursor-pointer hover:bg-[#b8c4ff] rounded-md" onClick={()=>{setDisplay(false)}}/>
					</div>
					<div className="px-2 ">	
						<div className="w-full h-1 bg-[#00288e] rounded-xl"/>
					</div>


				</motion.div> 
				}
			</AnimatePresence>
		</div>
	)
}

