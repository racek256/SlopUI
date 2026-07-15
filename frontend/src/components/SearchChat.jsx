import { motion, AnimatePresence } from "framer-motion"
import Search from "../Assets/search.svg?react"
import Close from "../Assets/close.svg?react"

import { useEffect, useRef } from "react"

export default function SearchChat({remove}){
	const ref = useRef()

	useEffect(()=>{
		function handleClick(e){
			if(!ref.current?.contains(e.target)){
				// clicked outside
				remove()
			}
		}
		document.addEventListener("pointerdown", handleClick)


	})


	return(
			<motion.div ref={ref} className="bg-[#fcf9f8] border-[#b8c4ff] border   shadow-card shadow-[#b8c4ff]/20 absolute w-1/4 h-92 rounded-2xl top-1/2 left-1/2 z-10000 -translate-x-1/2 -translate-y-1/2 flex-col flex"
			initial={{opacity:0,y:10}}
			animate={{opacity:1,y:0}}
			exit={{opacity:0, y:10}}>
				<div className="flex h-12 p-2">	
					<Search className="h-full w-12"/>	
					<input autoFocus className="grow h-full  text-xl" placeholder="Search"/>
					<Close className="h-full w-8 transition-all cursor-pointer hover:bg-[#b8c4ff] rounded-md" onClick={()=>{remove()}}/>
				</div>
				<div className="px-2 ">	
					<div className="w-full h-1 bg-[#00288e] rounded-xl"/>
				</div>
				<section className="flex flex-col p-2  justify-center">
					<div className="w-full h-12  text-lg hover:bg-[#eae7e6] transition-all rounded-lg flex items-center ">
						<p className="">Chat about potatos</p>	
					</div>	
					<div className="w-full h-12  text-lg hover:bg-[#eae7e6] transition-all rounded-lg flex items-center ">
						<p className="">Chat about apples</p>	
					</div>	
				</section>
			</motion.div>
	)
}
