import { useEffect } from "react"
import { useState } from "react"

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Reasoning from "./Reasoning"


import { motion } from "framer-motion"
export default function Message({message}){

	if (message.role === "user") {
	  return (
		<motion.div
		  className="border-[#b8c4ff] border bg-white w-max max-w-2/3 min-w-0 self-end my-2 rounded-2xl p-4 px-5"
		  initial={!message.instant && { opacity: 0, y: 10 }}
		  animate={{ opacity: 1, y: 0 }}
		>
		  <p className="whitespace-pre-wrap break-words">
			{message.content}
		  </p>
		</motion.div>
	  );
	}else{	
		return(
			<div className="min-w-full">
			<motion.div className="border-[#b8c4ff] border bg-white  h-max w-max text-base rounded-2xl p-4 px-5 self-start max-w-full   my-2 transition-all "
			initial={!message.instant && {
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
			<Reasoning message={message}/>	

					<div className={`overflow-hidden   relative  flex prose h-max  transition-all w-full`}>
					<div>
			{/*<div className={`w-8 h-8   animate-spin  ${message.content != "" ? "-ml-12" : ""} m-1 transition-all bg-black loading text-base whitespace-pre-wrap`}/>*/}
						</div>
					<div className=" w-full inline">	
						<ReactMarkdown remarkPlugins={[remarkGfm]}>	
						{message.content}
						</ReactMarkdown >
					</div>
				</div>
							
			</motion.div>
			</div>
		)
	}
}
