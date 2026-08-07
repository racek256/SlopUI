import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
import { useEffect } from "react"
import { useRef } from "react";


export default function Chat({expanded, setExpanded, chat_id, setChatID}){
	const [active, setActive] = useState(false)
	const [history, updateHistory] = useState([])
	const [model, setModel] = useState({name:"deepseek v4 flash", id:"opencode-go/deepseek-v4-flash"})
	const chat = useRef()

	// Reconstruct history in current branch
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

	// Load selected chat
	useEffect(()=>{
		async function loadChat(){
			const data = await fetch(`/api/chat/${chat_id}`)
			if (data.ok){
				const response = JSON.parse((await data.json()).chat)
				console.log(response)
				const new_history = construct(response).map(m => ({ ...m, instant: true }))
				updateHistory(new_history)
			}
		}
		if(chat_id){
			loadChat()
			fastScrollDown()
		}else if (chat_id == null){
			updateHistory([])
			setChatID(undefined)
			setActive(false)
		}
	
	},[chat_id])

	function fastScrollDown(){
		const el = chat.current;
		if(el){
			el.scrollTo({
				top: el.scrollHeight,
				behavior: 'instant'
			})
		}
	}

	// scroll down
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
			}else if (content.reasoning_content){
				updateHistory(prev =>{
					const updated = [...prev]
					if(updated[updated.length-1]?.reason_chain[updated[updated.length-1].reason_chain.length-1]?.type == "reason"){
						// Push streamed text to reasoning
						console.log("pushing to existing reasoning element")
						let element = updated[updated.length-1].reason_chain[updated[updated.length-1]?.reason_chain.length-1]
						element.content += content.reasoning_content
						updated[updated.length-1].reason_chain[updated[updated.length-1]?.reason_chain.length-1] = element
					}else{
						// Push new element to array and include reasoning
						console.log("creating new reasoning element")
						const element = {
							type:"reason",
							content:content.resoning_content
						}
						updated[updated.length-1].reason_chain.push(element)
					}	
					return updated

				})
			}else if (content.tool_calls[0].function.name =="websearch"){
				updateHistory(prev =>{
					const updated = [...prev]
					console.log("creating new reasoning element (websearch)")
					const element = {
						type:"websearch",
					}
					updated[updated.length-1].reason_chain.push(element)
					return updated
				})

			}
		}

		console.log(chat_id)
		const response = await fetch(`/api/chat/send`,{
			method:"POST",
			headers:{"Content-Type":"application/json"},
			body:JSON.stringify({content,chat_id:chat_id?.toString(),model:model.id}),
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
			content:"",
			reason_chain:[]
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
		<div className="w-full h-screen flex-col flex py-4 pb-0 z-100 items-center overflow-hidden">
			<div ref={chat} className={`w-full ${expanded || history.length>0 ? "h-full" : "h-1/2"} transition-all duration-500 overflow-y-scroll flex flex-col items-center `}>
				<div className={`min-w-9/16 w-204 max-w-full transition-all  duration-500  py-12  h-full flex flex-col`}>
					{history.map((e,i)=>(
						<Message key={i} message={e}></Message>
					))}
					<div className="h-24 w-full  shrink-0"></div>
		
			
				</div>
			</div>
			<TextThing expanded={expanded} active={active} sendMessage={sendMessage} interrupt={interrupt} model={model} setModel={setModel}/> {/* Not centered for now fix in future*/}
		</div>
	)
}
