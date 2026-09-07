import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
import { useEffect } from "react"
import { useRef, useLayoutEffect } from "react";
import Failed from "./Failed";


export default function Chat({expanded, setExpanded, chat_id, setChatID}){
	const [active, setActive] = useState(false)
	const [history, updateHistory] = useState([])
	const [model, setModel] = useState({name:"loading...", id:""})
	const [models, setModels] = useState([])

	const chat = useRef()
	const prevHistoryLen = useRef(0)


	async function getModels(){
		const data = await fetch("/api/chat/models")
		if (data.ok){
			const response = await data.json()
			console.log(response)
			setModels(response.models)
			let found = -1
			response.models.forEach((e,i) => {
				if (e.default == true){
					found = i
				}
				
			});
			if (found != -1){
				setModel({
					"id":response.models[found].id,
					"name":response.models[found].name
				})
			}else{
				setModel({
					"id":response.models[i].id,
					"name":response.models[i].name
				})
			}
		}
	}

	useEffect(()=>{
		getModels()
	},[])

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
			}else if (content.reasoning_content) {
			  updateHistory(prev => {
				const updated = [...prev]
				const lastMsg = updated[updated.length - 1]
				const chain = lastMsg.reason_chain
				const lastEl = chain[chain.length - 1]

				let newChain
				if (lastEl?.type === "reason") {
				  newChain = [
					...chain.slice(0, -1),
					{ ...lastEl, content: lastEl.content + content.reasoning_content, startTime: lastEl.startTime }
				  ]
				} else {
				  newChain = [...chain, { type: "reason", content: content.reasoning_content, startTime: Date.now() }]
				}

				updated[updated.length - 1] = { ...lastMsg, reason_chain: newChain }
				return updated
			  })
			}
			else if (content.tool_calls[0].function.name){
				updateHistory(prev =>{
					if (prev[prev.length-1].reason_chain[prev[prev.length-1].reason_chain.length-1].type != content.tool_calls[0].function.name){
						const updated = [...prev]
						console.log("creating new reasoning element")
						const element = {
							type:content.tool_calls[0].function.name,
							startTime:Date.now()
						}
						updated[updated.length-1].reason_chain.push(element)
						return updated
					}
					else{
						return prev
					}
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
		if (!response.ok){
			setActive(false)
			// Nuke AI's resposne
			const old_his = [...history]
			old_his.pop()
			updateHistory(old_his)
		}


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

	async function resendMessage(){
		const oldH = [...history]
		oldH.push({
			role:"ai",
			content:"",
			reason_chain:[]
		})
		updateHistory(oldH)	
		setActive(true)
		generate("[REGEN_USER_MESSAGE]")
		setTimeout(()=>{
			scrollDown()
		},500)
	}
	
	async function sendMessage(message,files){
		// File preprocessing 
		const parsed_files = await Promise.all(files.map(async e => {
			if (e.type.includes("text/")){
				return { name: e.name, body: await e.text() }
			} else if (e.type.includes("image/")){
				const dataUrl = await new Promise((resolve, reject) => {
					const reader = new FileReader();
					reader.onload = () => resolve(reader.result);
					reader.onerror = reject;
					reader.readAsDataURL(e);
				});
				return { name: e.name, body: dataUrl }
			}
		}));


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
					{/* last message = user && generating = false  */}
					{!active && history[history?.length-1]?.role == "user" && <Failed regen={resendMessage}/>}
					<div className="h-6 sm:h-24 w-full  shrink-0"></div>
		
			
				</div>
			</div>
			<TextThing expanded={expanded} active={active} sendMessage={sendMessage} interrupt={interrupt} model={model} setModel={setModel} models={models}/> 
		</div>
	)
}
