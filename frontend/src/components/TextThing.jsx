import { useRef } from "react";
import ModelSelector from "./ModelSelector";
import Send from "../Assets/send.svg?react";
import Stop from "../Assets/stop.svg?react"
import Add from "../Assets/add.svg?react"
import Close from "../Assets/close.svg?react"
import { useState } from "react";
import { useEffect } from "react";


export default function TextThing({sendMessage, active, interrupt, expanded, model,setModel, models}) {
	const inputRef = useRef(null)
	const [files, setFiles] = useState([]);

	function addFile(file){
		let old_files =[...files]
		old_files.push(file)
		setFiles(old_files)
	}


	useEffect(()=>{
		console.log("file has changed")
		console.log(files)
	},[files])

	const text = useRef()
	function send(button){
			console.log(text)
			if (!active){
				const message = text.current.value
				if(message !=""){
					sendMessage(message, files)
					text.current.value = ""
				}
			}else{
				if(button){
					interrupt()	
				}
			}

	}
	return (
		<div className="relative bottom-0  w-204 min-w-9/16 max-w-full transition-all">
		
			<div className="bg-white  flex-col border border-[#b8c4ff] w-full  transition-all py-4 px-4 shadow-[#b8c4ff]/20 shadow flex z-1 rounded-2xl relative min-w-9/16  max-w-full -translate-y-4  [box-shadow:0_-6px_8px_-3px_rgba(0,0,0,0.2)]" 
			onDragOver={e => e.preventDefault()}	
			onDrop={e=>{
				addFile(e.dataTransfer.files[0])
				e.preventDefault()
			}}>
				<input
			ref={inputRef}
			type="file"
			className="hidden"
			onChange={e=>{addFile(e.target.files?.[0] ?? null)}}
			/>
				<div className={`flex grow ${files.length > 0 ? 'h-12' : 'h-0'} transition-all  overflow-hidden items-center `}>
							{files.map((e,i)=>(
								<div className="flex border p-1 items-center rounded-md mx-1 ">
								<div key={i} className="h-9 w-max max-w-32  text-sm flex items-center truncate overflow-hidden  rounded-md">{e.name}</div>
								<Close className="cursor-pointer" onClick={()=>{
									let old_arr = [...files]
									let index = old_arr.findIndex(f => f.name == e.name)
									old_arr.splice(index,1)
									setFiles(old_arr)
								}}/>
								</div>
							))}
						</div>
				<textarea autoFocus ref={text}   onKeyDown={e => {
					if (e.key == "Enter"){
						e.preventDefault()
						send()
					}
				}} className="bg-white w-full z-2  field-sizing-content max-h-64  resize-none text-2xl   " placeholder="Ask anything" />
				<div className="flex justify-between items-center h-14 w-full overflow-hidden">
					{/* Starting part */}
					<div className="flex min-w-0 flex-1 items-center overflow-hidden">
						<Add className="flex-none h-12 aspect-square hover:bg-[#b8c4ff] cursor-pointer rounded-xl" onClick={()=>{
							console.log("clicky click")
							inputRef.current?.click()
						}}/>

					</div>
					
					{/* Ending part */}
					<div className=" flex flex-none flex-row-reverse items-center">	
						<div onClick={()=>{
							send(true)
						}} className={`send-btn h-12 w-12   ${!active ? "bg-[#00288e]" : "bg-[#b8c4ff]"}  z-10 cursor-pointer rounded-xl flex items-center justify-center p-3`}>
							{!active ? <Send className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none" />
							:  <Stop className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none"  />
							}
						</div>
						<ModelSelector expanded={expanded} model={model} setModel={setModel} models={models}/>
				</div>
			
				</div>
			</div>
		</div>
	)
}
