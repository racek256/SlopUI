import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
import { useEffect } from "react"
import { useRef, useLayoutEffect } from "react";


export default function Chat({expanded, setExpanded, chat_id, setChatID}){
	const [active, setActive] = useState(false)
	const [history, updateHistory] = useState([])
	const [model, setModel] = useState({name:"Muse Spark 1.2", id:"opencode-go/muse-spark-1.2-contributor"})
	const chat = useRef()
	const prevHistoryLen = useRef(0)

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
				prevHistoryLen.current = 0
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



	useLayoutEffect(() => {
	  const el = chat.current
	  if (!el || history.length === 0) return

	  const newMessage = history.length !== prevHistoryLen.current
	  prevHistoryLen.current = history.length

	  if (newMessage || el.scrollHeight - el.scrollTop - el.clientHeight < 50) {
		  el.scrollTop = el.scrollHeight   // instant, no smooth, no transition
	  }
	}, [history])

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
			}else if (content.tool_calls[0].function.name){
				updateHistory(prev =>{
					const updated = [...prev]
					console.log("creating new reasoning element")
					const element = {
						type:content.tool_calls[0].function.name,
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
		<div className="w-full h-dvh flex-col flex py-4 pb-0 z-100 items-center overflow-hidden">
			<div ref={chat} className={`w-full ${expanded || history.length>0 ? "sm:h-full" : "sm:h-1/2"} h-full overflow-y-scroll flex flex-col items-center transition-all duration-500 `}>
				<div className={`min-w-9/16 w-204 max-w-full   py-12   flex flex-col`}>
					{history.map((e,i)=>(
						<Message key={i} message={e}></Message>
					))}
					<div className="h-6 sm:h-24 w-full  shrink-0"></div>
		
			
				</div>
			</div>
			<TextThing expanded={expanded} active={active} sendMessage={sendMessage} interrupt={interrupt} model={model} setModel={setModel}/> {/* Not centered for now fix in future*/}
		</div>
	)
}
