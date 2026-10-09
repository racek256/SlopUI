import { motion, AnimatePresence } from "framer-motion"
import Search from "../Assets/search.svg?react"
import Close from "../Assets/close.svg?react"

import { useEffect, useRef } from "react"
import { useState } from "react"

export default function SearchChat({remove, chats, loadChat}){
	const ref = useRef()
	const [query, setQuery] = useState("")
	const removeRef = useRef(remove)
	removeRef.current = remove

	useEffect(()=>{
		const node = ref.current
		if(!node) return

		function handleClick(e){
			if(!node.contains(e.target)){
				// clicked outside
				e.stopPropagation()
				removeRef.current?.()
			}
		}
		document.addEventListener("pointerdown", handleClick)
		return ()=> document.removeEventListener("pointerdown", handleClick)
	}, [])


	return(
			<motion.div ref={ref} className="bg-secondary min-w-72 border text-text border-accent   shadow-card shadow-accent absolute   w-1/4 h-92 rounded-2xl top-1/2 left-1/2 z-10000 -translate-x-1/2  -translate-y-1/2 flex-col flex"
			initial={{opacity:0,y:10}}
			animate={{opacity:1,y:0}}
			exit={{opacity:0, y:10}}>
				<div className="flex h-12 p-2">	
					<Search className="h-full w-12 fill-text"/>	
					<input  value={query} onChange={e=>{
						setQuery(e.target.value)
					}}  className="grow h-full  text-xl" placeholder="Search"/>
					<Close className="h-full w-8 transition-all cursor-pointer hover:bg-hover fill-text rounded-md" onClick={()=>{remove()}}/>
				</div>

				<div className="px-2 ">	
					<div className="w-full h-1 bg-[#00288e] rounded-xl"/>
				</div>

				<section className=" p-2  justify-center grow overflow-y-auto">
					{chats.map((e,i)=>{
						if(e.name.toLowerCase().includes(query.toLowerCase())){
							return(
								<div key={i} className="w-full h-12  text-lg hover:bg-hover cursor-pointer transition-all rounded-lg flex items-center " onClick={()=>{
							loadChat(e.id)
							remove()
						}}>
						<p>{e.name}</p>	
					</div>
							)
						}
						
					})}	
				</section>
			</motion.div>
	)
}
