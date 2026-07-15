import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
import { useEffect } from "react"
export default function Chat({expanded, setExpanded}){
	const [active, setActive] = useState(false)
	const [history, updateHistory] = useState([])
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
			<div className={`w-full ${expanded || history.length>0 ? "h-full" : "h-1/2"} transition-all duration-500 overflow-y-scroll flex flex-col items-center`}>
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




