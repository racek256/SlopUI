import Search from '../Assets/search.svg?react'
import { AnimatePresence, motion } from 'framer-motion'

export default function Reasoning({ message }) {


	return <div className="flex flex-col">
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
								transition={{duration:0.5}}
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
								transition={{duration:0.5}}
								key="websearch"
								className="  bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
								<Search fill="black" className="shrink-0 animate-pulse size-8 block" /> Websearch</motion.div>)
					}
				} else if (!message.content) {
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
							transition={{duration:0.5}}
							key="waking"

							className="  bg-[#b8c4ff] w-max h-max rounded-lg mb-2 text-center flex items-center justify-center  text-black text-xl px-2 py-1">
							<div className="w-6 h-6 m-1 animate-spin transition-all bg-black loading" /> Waking up</motion.div>

					)
				}

			})()}
		</AnimatePresence>

	</div>
}
