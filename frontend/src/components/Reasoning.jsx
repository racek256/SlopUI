import { useState, useEffect } from 'react'
import Search from '../Assets/search.svg?react'
import Webfetch from '../Assets/webfetch.svg?react'
import { AnimatePresence, motion } from 'framer-motion'
import { useRef } from 'react'

export default function Reasoning({ message }) {
	const [hovered, setHovered] = useState(false)

	return <div className="flex flex-col reason-selector" onMouseOver={()=>{
			setHovered(true)
		}}
		onMouseOut={()=>{
			setHovered(false)
		}}>
		<AnimatePresence mode="wait">
		{hovered && <ReasonHover message={message}/>}
		</AnimatePresence>
		<AnimatePresence mode="wait">
			{(() => {
				if (message?.reason_chain?.length > 0 && !message.content) {
					const reason = message.reason_chain[message.reason_chain.length - 1]
					console.log("reason chain element")
					console.log(reason)
					if (reason?.type == "reason") {
						return (
							<motion.div
								initial={{
									y: 10,
									opacity: 0
								}}
								animate={{
									y: 0,
									opacity: 1
								}}
								exit={{
									y: -10,
									opacity: 0
								}}
								transition={{ duration: 0.5 }}
								key="reason"
								className=" bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
								<div className="w-6 h-6 m-1 animate-spin transition-all bg-black loading" /> Reasoning</motion.div>

						)
					} else if (reason?.type == "websearch") {
						return (
							<motion.div
								initial={{
									y: 10,
									opacity: 0
								}}
								animate={{
									y: 0,
									opacity: 1
								}}
								exit={{
									y: -10,
									opacity: 0
								}}
								transition={{ duration: 0.5 }}
								key="websearch"
								className="  bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
								<Search fill="black" className="shrink-0 animate-pulse size-8 block" /> Websearch</motion.div>)
					} else if (reason?.type == "webfetch") {
					return (
						<motion.div
							initial={{
								y: 10,
								opacity: 0
							}}
							animate={{
								y: 0,
								opacity: 1
							}}
							exit={{
								y: -10,
								opacity: 0
							}}
							transition={{ duration: 0.5 }}
							key="webfetch"
							className="  bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
							<Webfetch fill="black" className="shrink-0 animate-pulse size-8 block" /> Webfetch</motion.div>)
				} 
				} else if(!message.content) {
					return (
						<motion.div
							initial={{
								y: 10,
								opacity: 0
							}}
							animate={{
								y: 0,
								opacity: 1
							}}
							exit={{
								y: -10,
								opacity: 0
							}}
							transition={{ duration: 0.5 }}
							key="waking"

							className="  bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
							<div className="w-6 h-6 m-1 animate-spin transition-all bg-black loading" /> Waking up</motion.div>

					)
				}
				

			})()}
		</AnimatePresence>

	</div>
}


function ReasonHover(message){
	console.log(message)
	const now = useNow()

		const reasonBar = useRef()


	useEffect(()=>{
		const el = reasonBar.current
			el.scrollTo({
				top: el.scrollHeight,
				behavior: 'instant'
			})
	},[message])



	return(
		<motion.div className='reason-box w-lg h-64 rounded-xl  z-200 border-[#b8c4ff] border bg-white  max-w-9/10          shadow-2xl  shadow-gray-300'
		initial={{
					opacity: 0
				}}
				animate={{
					opacity: 1
				}}
				exit={{
					opacity: 0
				}}
				transition={{duration:0.1}}>
		<div ref={reasonBar} className='flex-col p-2 text-sm overflow-y-auto h-full'>
		{message?.message?.reason_chain?.map((e,i)=>{
			console.log("rendering this shit")
			console.log(e)
			let stoptime = now
			if (message.message.reason_chain[i+1]){
				stoptime = message.message.reason_chain[i+1].startTime

			}
			if (e.type == "reason"){
				return(
					<div>{e?.content}</div>
				)
			}else{
				return(
					<div className='flex items-center'>
						<div className='p-1 font-bold text-md'>websearch</div>
						<p className='mx-2'>{Math.round((stoptime - e.startTime)*10/1000)/10}s</p>
					</div>
				)
			}
		})}
		</div>

		</motion.div>)
}
function useNow(intervalMs = 100) {
	const [now, setNow] = useState(Date.now());
	useEffect(() => {
		const id = setInterval(() => setNow(Date.now()), intervalMs);
		return () => clearInterval(id);
	}, [intervalMs]);
	return now;
}
