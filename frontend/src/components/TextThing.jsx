import Send from "../Assets/send.svg?react";


export default function TextThing({setExpanded, sendMessage}) {
	return (
		<div className="bg-white  z-[1] rounded-2xl relative">
			<textarea autoFocus onKeyDown={e => {
				if(e.key=="Enter"){
					e.preventDefault()
					const message = e.target.value
					console.log("Alauh Ahbar")
					setExpanded(true)
					sendMessage(message)
					e.target.value = ""

				}
			}} className="bg-white w-full z-[2] py-4 px-8 rounded-2xl resize-none text-2xl border border-[#b8c4ff] shadow-[#b8c4ff]/20 shadow " placeholder="Ask anything" />
			<div className="send-btn h-12 w-12 absolute bottom-2 right-2 bg-[#00288e] z-[10] cursor-pointer rounded-xl flex items-center justify-center p-3">
				<Send className="send-icon w-full h-full fill-[#e3e3e3] pointer-events-none" />
			</div>
		</div>
	)
}
