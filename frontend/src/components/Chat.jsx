import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
import { useEffect } from "react"
import { useRef } from "react";
const apiUrl = import.meta.env.VITE_API_URL;


export default function Chat({expanded, setExpanded, chat_id, setChatID}){
	const [active, setActive] = useState(false)
	const [history, updateHistory] = useState([])
	const chat = useRef()
	function construct(data){
		let currMSG = data.current_message_id
		const new_arr = []

		while (true){
			const message = data.messages.find(e => e.id == currMSG)
			new_arr.push(message)
			if (message.parent_message_id){
				currMSG = message.parent_message_id
			}
			else{
				break;
			}
		}
		new_arr.reverse()
		return new_arr

	}


	useEffect(()=>{
		async function loadChat(){
			const data = await fetch(`/api/chat/${chat_id}`)
			if (data.ok){
				const response = JSON.parse((await data.json()).chat)
				console.log(response)
				const new_history = construct(response)
				updateHistory(new_history)
			}
		}
		if(chat_id){
			loadChat()
		}else if (chat_id == null){
			updateHistory([])
			setChatID(undefined)
			setActive(false)
		}
	
	},[chat_id])

	function scrollDown(){
		const el = chat.current;
		if(el){
			el.scrollTo({
				top: el.scrollHeight,
				behavior: 'smooth'
			})
		}
	}




	// AI request
	async function generate(content){	
		function onObject(content) {
			console.log(content)
			if(content.chat_id){
				console.log("chat_id received")
				setChatID(content.chat_id)
				setActive(false)
			}else if (content.content){
			  updateHistory(prev => {
				const updated = [...prev]
				const last = updated[updated.length - 1]
				updated[updated.length - 1] = {
				  ...last,
				  content: last.content + content.content
				}
				return updated
			  })
			}
		}
		console.log(chat_id)
		const response = await fetch(`/api/chat/send`,{
			method:"POST",
			headers:{"Content-Type":"application/json"},
			body:JSON.stringify({content,chat_id:chat_id?.toString(),model:"opencode-zen/deepseek-v4-flash-free"}),
			credentials:"include"
		})

		// Check if response okay 


		const reader = response.body.getReader()
		const decoder = new TextDecoder();
		let buffer = '';
		while (true){
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, {stream:true})
			const lines = buffer.split('\n')
			buffer=lines.pop();

			for (const line of lines){
				const trimmed = line.trim();
				if (!trimmed) continue;
				try {
					onObject(JSON.parse(trimmed))
				}
				catch (err){
					console.error("bad JSON line:", trimmed, err)
				}
			}
		}

		if (buffer.trim()){
			try {
				onObject(JSON.parse(buffer.trim()))
			} catch (err){
				console.error('Bad final JSON line:', buffer, err)
			}

		} 		
	}







	useEffect(()=>{
		if(history.length>0){
			setExpanded(true)
		}else{
			setExpanded(false)
		}

	},[history])

	
	function sendMessage(message){
		const oldH = [...history]
		// add user message
		oldH.push({
			role:"user",
			content:message
		})
		// add AI message
		oldH.push({
			role:"ai",
			content:""
		})
		updateHistory(oldH)	
		setActive(true)

		generate(message)
		setTimeout(()=>{
			scrollDown()
		},500)

	}
	function interrupt(){
		console.log('interruptting')
		setActive(false)
		const historyClone = [...history]
		historyClone.pop()
		historyClone.pop()
		updateHistory(historyClone)

	}

	return(
		<div className="w-full h-screen flex-col flex py-4  z-100 items-center">
			<div ref={chat} className={`w-full ${expanded || history.length>0 ? "h-full" : "h-1/2"} transition-all duration-500 overflow-y-scroll flex flex-col items-center`}>
				<div className={`w-1/2 transition-all  duration-500  py-12  h-full flex flex-col`}>
					{history.map((e,i)=>(
						<Message key={i} content={e.content} role={e.role} ></Message>
					))}
					<div className="h-24 w-full  shrink-0"></div>
		
			
				</div>
			</div>
			<TextThing expanded={expanded} active={active} sendMessage={sendMessage} interrupt={interrupt}/> {/* Not centered for now fix in future*/}
		</div>
	)
}
