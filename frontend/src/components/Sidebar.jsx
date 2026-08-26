import Edit from '../Assets/edit.svg?react'
import Search from'../Assets/search.svg?react'
import Menu from'../Assets/menu.svg?react'
import { useState, useEffect, useRef } from 'react'

export default function Sidebar({search,chats, loadChat, newChat}){
	const [expanded, setExpanded] = useState(false)
	console.log(chats)
		const ref = useRef()

	useEffect(()=>{
		function handleClick(e){
			if(!ref.current?.contains(e.target)){
				// clicked outside
			setExpanded(false)	
			}
		}
		document.addEventListener("pointerdown", handleClick)


	})
	return(
		<>
			<div   className='absolute cursor-pointer z-120 sm:hidden p-2' onClick={()=>{
					setExpanded(!expanded)}}>
			<Menu fill="black"  className="shrink-0 size-8 cursor-pointer"
				/>
			</div>

			<div ref={ref} className='relative z-150 shrink-0'>
			<section className={`sidebar w-69 h-dvh overflow-hidden bg-white flex flex-col items-center inset-y-1 fixed transition-all ${expanded ? "translate-x-0" : "-translate-x-full sm:translate-x-0"} sm:static`}>
				{/* Heading */}
				<div className="w-61 h-14  mt-3 bg-[#fcf9f8] shadow-card rounded-xl HeadText text-4xl flex items-center justify-center">
					<p className="text-[#00288e]">Slop</p>
					<p className="text-[#1c1b1b]">UI</p>
				</div>	
				{/* separator */}
				<div className='w-61 my-1 h-1 rounded bg-[#00288e] '/>
				{/* new chat button */}
				<div className="w-61    mt-2 p-1 bg-[#eae7e6] transition-all cursor-pointer  rounded-xl HeadText text-xl flex items-center " onClick={()=>{newChat(); setExpanded(false)}}>
						<Edit fill="black"  className="shrink-0 size-8 block"/>
						<p className=" ms-2 text-[#1c1b1b] select-none">new chat</p>
				</div>
				{/* Search button */}
			{/*<div className="w-61    mt-2 p-1  hover:bg-[#eae7e6] transition-all cursor-pointer  rounded-xl HeadText text-xl flex items-center " onClick={()=>{search()}}>
						<Search fill="black"  className="shrink-0 size-8 block"/>
						<p className=" ms-2 text-[#1c1b1b]">search</p>
				</div>*/}
				{/* spearator */}
				<div className='flex w-full items-center px-2'>
					<div className='grow h-1 bg-black rounded-r-xl'/>
						<p className='mx-2'>Chats</p>
					<div className='grow h-1 bg-black rounded-l-xl'/>
				</div>
				{/* Chats */}

				<section className='flex flex-col mt-2 w-full px-1 h-full overflow-y-auto'> {/* Chats */}
					{chats.map((e,i)=>(
						<div className='w-full p-1 px-4 py-2  hover:bg-[#dad7d6] transition-none  cursor-pointer  rounded-sm  ' key={i} onClick={()=>{loadChat(e.id); setExpanded(false)}}>{e.name}</div>
					))}
				</section>
			</section>
			</div>
		</>
	)
}

