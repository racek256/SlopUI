import { useRef } from "react";
import ModelSelector from "./ModelSelector";
import Send from "../Assets/send.svg?react";
import Stop from "../Assets/stop.svg?react"


export default function TextThing({sendMessage, active, interrupt, expanded, model,setModel}) {


	const text = useRef()
	function send(button){
			console.log(text)
			if (!active){
				const message = text.current.value
				if(message !=""){
					sendMessage(message)
					text.current.value = ""
				}
			}else{
				if(button){
					interrupt()	
				}
			}

	}
	return (
		<div className="bg-white  z-1 rounded-2xl relative min-w-9/16 w-204 max-w-full -translate-y-4 shadow-none [box-shadow:0_-6px_8px_-3px_rgba(0,0,0,0.2)]">
			<textarea autoFocus ref={text}  onKeyDown={e => {
				if (e.key == "Enter"){
					e.preventDefault()
					send()
				}
			}} className="bg-white w-full z-2 py-4 px-8 rounded-2xl resize-none text-2xl border border-[#b8c4ff] shadow-[#b8c4ff]/20 shadow " placeholder="Ask anything" />

			<div className="absolute flex bottom-2 right-2 flex-row-reverse"	>	
				<div onClick={()=>{
					send(true)
				}} className={`send-btn h-12 w-12   ${!active ? "bg-[#00288e]" : "bg-[#b8c4ff]"}  z-10 cursor-pointer rounded-xl flex items-center justify-center p-3`}>
					{!active ? <Send className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none" />
					:  <Stop className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none"  />
					}	
				</div>
				<ModelSelector expanded={expanded} model={model} setModel={setModel}/>
		
			</div>
		</div>
	)
}
