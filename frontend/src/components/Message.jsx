
import Close from "../Assets/close.svg?react"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Reasoning from "./Reasoning"


import { motion } from "framer-motion"
export default function Message({ message,files }) {



	if (message.role === "user") {
		return (
			<motion.div
				className="border-[#b8c4ff] border bg-white w-max max-w-2/3 min-w-0 self-end my-2 text-sm sm:text-base rounded-2xl "
				initial={!message.instant && { opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
			>

				<p className="whitespace-pre-wrap wrap-break-words p-4">
					{message.content}
				</p>


				{files.length > 0 &&
					<div>
						<div className="flex px-2 h-3 w-full items-center">
							<div className=' h-1 rounded w-1/20 bg-black' />
							<p className="mx-2">files</p>
							<div className=' h-1 rounded w-full bg-black' />
						</div>
						<div className={`flex grow ${files.length > 0 ? 'h-12' : 'h-0'} transition-all p-2 my-2  overflow-hidden items-center `}>
							{files?.map((e, i) => (
								<div className="flex border p-1 items-center rounded-md mx-1 ">
									<div key={i} className="h-9 w-max max-w-32  text-sm flex items-center truncate overflow-hidden  rounded-md hover:text-[8px] transition-all cursor-select hover:p-2">{e.name}</div>
								</div>

							))}
						</div>

					</div>
				}

			</motion.div>
		);
	} else {
		return (
			<div className="min-w-full">
				<motion.div className="border-[#b8c4ff] border bg-white  h-max w-max text-sm sm:text-base rounded-2xl p-4 px-5 self-start max-w-full   my-2 transition-all "
					initial={!message.instant && {
						opacity: 0,
						y: 10
					}}
					animate={{
						opacity: 1,
						y: 0
					}}
					transition={{
						delay: 1
					}}
				>
					<Reasoning message={message} />
					<div className={`overflow-hidden   relative  flex prose h-max  transition-all w-full p-0`}>
						<div>
							{/*<div className={`w-8 h-8   animate-spin  ${message.content != "" ? "-ml-12" : ""} m-1 transition-all bg-black loading text-base whitespace-pre-wrap`}/>*/}
						</div>
						<div className=" w-full inline p-0">
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
