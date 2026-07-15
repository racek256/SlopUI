import { useEffect } from "react"
import { useState } from "react"


import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'



import { motion } from "framer-motion"
export default function Message({content, role}){
	const [text,updateText] = useState("")

	useEffect(()=>{
		if(content != ""){
			setInterval(()=>{
				updateText(content)
			},150)
		}
	},[content])

	if (role =="user"){
		return(
			<motion.div className="border-[#b8c4ff] border bg-white w-max text-xl rounded-2xl p-4 px-5 self-end max-w-2/3 my-2"
			initial={{opacity:0, y:10}}
			animate={{opacity:1,y:0}}
			>
			<p className="">	
			{content}
			</p>

			</motion.div>
		)
	}else{	
		return(
			<motion.div className="border-[#b8c4ff] border bg-white  h-max w-max text-base rounded-2xl p-4 px-5 self-start  max-w-2/3 my-2 "
			initial={{
				opacity:0,
				y:10
			}}
			animate={{
				opacity:1,
				y:0
			}}
			transition={{
				delay:1
			}}
			>

					<div className={`overflow-hidden   relative  flex prose h-max  `}>
					<div>
							<div className={`w-8 h-8   animate-spin  ${content != "" ? "-ml-12" : ""} m-1 transition-all bg-black loading text-base whitespace-pre-wrap`}/>
						</div>
					<div className="inline">	
						<ReactMarkdown remarkPlugins={[remarkGfm]}>	
						{text}
						</ReactMarkdown >
					</div>
				</div>
							
			</motion.div>
		)
	}
}
