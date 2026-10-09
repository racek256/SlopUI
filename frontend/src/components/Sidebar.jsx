import Edit from '../Assets/edit.svg?react'
import Pin from '../Assets/pin.svg?react'
import Unpin from '../Assets/unpin.svg?react'
import Search from '../Assets/search.svg?react'
import Menu from '../Assets/menu.svg?react'
import Logo from '../Assets/logo.svg?react'
import { useState, useEffect, useRef } from 'react'

export default function Sidebar({ search, chats, loadChat, newChat, loadChats }) {
	const [expanded, setExpanded] = useState(false)
	console.log(chats)
	const ref = useRef()






	async function pinChat(chat_id) {
		await fetch("/api/chat/pin", {
			method: "POST",
			headers: { "content-type": "application/json" },
			body: JSON.stringify({
				chat_id: chat_id.toString()
			})
		})
		loadChats()
	}

	useEffect(() => {
		function handleClick(e) {
			if (!ref.current?.contains(e.target)) {
				// clicked outside
			 	e.stopPropagation()
				setExpanded(false)
			}
		}
		document.addEventListener("pointerdown", handleClick)


	})
	return (
		<>
			<div className='absolute cursor-pointer z-110 sm:hidden p-2' onClick={() => {
				setExpanded(!expanded)
			}}>
				<Menu  className="shrink-0 fill-text size-8 cursor-pointer"
				/>
			</div>

			<div ref={ref} className='relative z-110 shrink-0 '>
				<section className={`bg-secondary text-text w-69 h-dvh overflow-hidden  flex flex-col items-center inset-y-1 fixed transition-all ${expanded ? "translate-x-0" : "-translate-x-full sm:translate-x-0"} sm:static`}>
					{/* Heading */}
					<Logo className="w-61 h-14 mt-3 mb-1 " />
					{/* separator */}
					{/*<div className='w-61 my-1 h-1 rounded bg-[#00288e] dark:bg-[#b8c4ff]'/>*/}
					{/* new chat button */}
					<div className="w-61    mt-2 p-1 bg-button text-text transition-all cursor-pointer  rounded-md HeadText text-xl flex items-center " onClick={() => { newChat(); setExpanded(false) }}>
						<Edit fill="" className="shrink-0  fill-text size-8 block" />
						<p className=" ms-2 text-text select-none">new chat</p>
					</div>
					{/* Search button */}
					<div className="w-61 bg-button mt-2 p-1   transition-all cursor-pointer  rounded-md HeadText text-xl flex items-center " onClick={() => { search() }}>
						<Search className="shrink-0 fill-text size-8 block" />
						<p className=" ms-2 text-text">search</p>
					</div>
					{/* spearator */}
					<div className='flex w-full items-center px-2'>
						<div className='grow h-1 bg-text  rounded-r-xl' />
						<p className='mx-2'>Chats</p>
						<div className='grow h-1 bg-text rounded-l-xl' />
					</div>
					{/* Chats */}

					<section className='flex flex-col mt-2 w-full px-1 h-full overflow-y-auto'> {/* Chats */}
						{chats.map((e, i) => (
							<div className='w-full group p-1 px-4 py-2  hover:bg-hover transition-none  cursor-pointer  rounded-sm  flex space-between justify-between'
								key={i} onClick={() => { loadChat(e.id); setExpanded(false) }}>
								<p>{e.name}</p>
								{!e.pinned ?
								<Pin onClick={a => {
									a.stopPropagation()
									
									pinChat(e.id)

								}} className="group-hover:opacity-50 opacity-0  rounded-md hover:bg-secondary  transition-colors" />	: <Unpin className="opacity-50 hover:bg-secondary rounded-md transition-colors" onClick={a=>{	
									a.stopPropagation()
									pinChat(e.id)
								}} />}
									</div>
						))}
					</section>
				</section>
			</div>
		</>
	)
}

