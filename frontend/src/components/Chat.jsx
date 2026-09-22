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

	const [failed, setFailed] = useState(false)

	useEffect(()=>{
		if (!active && history?.length > 0 && history[history?.length-1]?.role == "user" && !failed ){
			// Attempt to register stream
			if(chat_id){
				const oldH = [...history]	
				// add AI message
				oldH.push({
					role:"ai",
					content:"",
					reason_chain:[]
				})
				setActive(true)
				updateHistory(oldH)
				generate(chat_id)
			}else{
			setFailed(true)

			}	
		}else{
			if (history[history?.length-1]?.role == "ai" || history?.length == 0 ){
				setFailed(false)
			}
		}
	},[active, history])


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
					"id":response.models[0].id,
					"name":response.models[0].name
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
				setFailed(false)
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
	async function generate(activeChatID){	

		function onObject(content) {
			console.log(content)
			if(content.chat_id){
				console.log("response finish received")
				setChatID(content.chat_id)
				setActive(false)
			}else if (content.content){
				// Received response
			  updateHistory(prev => {
				// Add resposne to message
				const updated = [...prev]
				const last = updated[updated.length - 1]
				updated[updated.length - 1] = {
				  ...last,
				  content: last.content + content.content
				}
				// Add response to reasoning chain
				const lastMsg = updated[updated.length - 1]
				const chain = lastMsg.reason_chain
				const lastEl = chain[chain.length - 1]

				let newChain
				if (lastEl?.type === "response") {
			      // El exists
				  newChain = [
					...chain.slice(0, -1),
					{ ...lastEl, content: lastEl.content + content.reasoning_content, startTime: lastEl.startTime }
				  ]
				} else {
				  // creating new Response El
				  newChain = [...chain, { type: "response", content: content.reasoning_content, startTime: Date.now() }]
				}
				updated[updated.length - 1] = { ...lastMsg, reason_chain: newChain }



				return updated
			  })
			}else if (content.reasoning_content) {
				// Received reasoning
			  updateHistory(prev => {
				const updated = [...prev]
				const lastMsg = updated[updated.length - 1]
				const chain = lastMsg.reason_chain
				const lastEl = chain[chain.length - 1]

				let newChain
				if (lastEl?.type === "reason") {
			      // Reasoning El exists
				  newChain = [
					...chain.slice(0, -1),
					{ ...lastEl, content: lastEl.content + content.reasoning_content, startTime: lastEl.startTime }
				  ]
				} else {
				  // Create new reasoning el
				  newChain = [...chain, { type: "reason", content: content.reasoning_content, startTime: Date.now() }]
				}

				updated[updated.length - 1] = { ...lastMsg, reason_chain: newChain }
				return updated
			  })
			}
			else if (content?.tool_calls != null && content.tool_calls[0]?.function?.name){
				// Received Tool call
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
		const response = await fetch(`/api/chat/get_stream`,{
			method:"POST",
			headers:{"Content-Type":"application/json"},
			body:JSON.stringify({chat_id:activeChatID.toString()}),
			credentials:"include"
		})

		// Check if response okay 
		if (!response.ok){
			setActive(false)
			// Nuke AI's resposne
			updateHistory(h=>{
				const old_his = [...h]
				old_his.pop()
				return old_his
			})
			setFailed(true)
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
		const response = await fetch(`/api/chat/send`,{
			method:"POST",
			headers:{"Content-Type":"application/json"},
			body:JSON.stringify({content:"[REGEN_USER_MESSAGE]",chat_id:chat_id?.toString(),model:model.id}),
			credentials:"include"
		})
		if (!response.ok){
			console.error("kabbom big no request careated")
		}
		const new_chatid = (await response.json()).gen_id
		if (new_chatid != chat_id){
			//setChatID(new_chatid)
		}
		generate(new_chatid)

		setTimeout(()=>{
			scrollDown()
		},500)
	}
	
	async function sendMessage(message,files){
		// File preprocessing 
		console.log("FILES UNHEER")
		console.log(files)
		const parsed_files = await Promise.all((files||[]).filter(Boolean).map(async e => {
			const mime = e.type || "";
			try {
				if (mime.includes("image/")){
					const dataUrl = await new Promise((resolve, reject) => {
						const reader = new FileReader();
						reader.onload = () => resolve(reader.result);
						reader.onerror = () => reject(reader.error);
						reader.readAsDataURL(e);
					});
					return { name: e.name, type: mime, body: dataUrl }
				}
				// Default: try to read as text (covers text/*, empty type, json, etc.)
				// Binary types (pdf/docx/zip/...) will still resolve, backend marks unsupported if needed
				return { name: e.name, type: mime, body: await e.text() }
			} catch(err) {
				console.error("file read failed:", e?.name, err);
				return { name: e?.name ?? "unknown", type: mime, body: "", error: String(err?.message ?? err) };
			}
		}));

		console.log("FILES HEEER:")
		console.log(parsed_files)

		const oldH = [...history]
		// add user message
		oldH.push({
			role:"user",
			content:message,
			files:parsed_files.map((e)=>{return {name:e.name}})
		})
		// add AI message
		oldH.push({
			role:"ai",
			content:"",
			reason_chain:[]
		})
		updateHistory(oldH)	
		setActive(true)

		// create request
		const response = await fetch(`/api/chat/send`,{
			method:"POST",
			headers:{"Content-Type":"application/json"},
			body:JSON.stringify({content:message,chat_id:chat_id?.toString(),model:model.id, files:parsed_files}),
			credentials:"include"
		})
		if (!response.ok){
			console.error("kabbom big no request careated")
		}
		const new_chatid = (await response.json()).gen_id
		if (new_chatid != chat_id){
			//setChatID(new_chatid)
		}
		

		// signup for stream
		generate(new_chatid)
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
						<Message key={i} message={e} files={e?.files || []}></Message>
					))}
					{/* last message = user && generating = false  */}
					{failed && <Failed regen={resendMessage}/>}
					<div className="h-6 sm:h-24 w-full  shrink-0"></div>
		
			
				</div>
			</div>
			<TextThing expanded={expanded} active={active} sendMessage={sendMessage} interrupt={interrupt} model={model} setModel={setModel} models={models}/> 
		</div>
	)
}
