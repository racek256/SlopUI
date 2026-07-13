import { useState } from "react"
import TextThing from "./TextThing"
import Message from "./Message"
export default function Chat({expanded, setExpanded}){
	const [history, updateHistory] = useState([])

	function sendMessage(message){
		const oldH = [...history]
		oldH.push({
			role:"user",
			content:message
		})
		updateHistory(oldH)
	}

	return(
		<div className="w-1/2 h-screen flex-col flex py-4 pt-12 z-100">
			<div className={` transition-all duration-500  ${expanded ? "h-full" : "h-1/2"} flex flex-col`}>
				{history.map(e=>(
					<Message role={e.role} >{e.content}</Message>
				))}
		
			</div>
			<TextThing setExpanded={setExpanded} sendMessage={sendMessage}/> {/* Not centered for now fix in future*/}
		</div>
	)
}
