import Sidebar from './components/Sidebar'
import Background from './components/Background'
import Chat from './components/Chat'
import SearchChat from './components/SearchChat'
import { useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import Login from './components/Login'
import { useEffect } from 'react'
import Cookies from 'js-cookie'


function App() {
	const [expanded, setExpanded] = useState(false)
	const [search, setSearch] = useState(false)
	const [loginWindow, toggleLoginWindow] = useState(false)
	const [chat_id, setChatId] = useState(undefined)
	const [chats, updateChats] = useState([])	



	async function loadChats(limit){
		const data = await fetch('/api/chat/')
		if (data.ok){
			const result = await data.json()
			console.log(result)
			updateChats(JSON.parse(result.chats))
		}
	}


	useEffect(()=>{
		loadChats()
	},[chat_id])








	useEffect(()=>{
		const token = Cookies.get("token")
		// Verify Token validity
		async function verifyToken(token){
			try{

			
			const response = await fetch(`/api/auth/verify`,{
				method:"POST",
				headers:{"Content-Type":"application/json",},
				body:JSON.stringify({token})
			})
			if (!response.ok){
				toggleLoginWindow(true)
			}
			}
			catch{
				toggleLoginWindow(true)
			}
		}
		if(!token){
			toggleLoginWindow(true)
		}else{
			verifyToken(token)
		}
	},[])


  return (
		<div className='flex h-dvh sm:p-0 p-2'>
		  <Sidebar search={()=>{setSearch(true)}} chats={chats} loadChat={(i)=>setChatId(i)} newChat={()=>{setChatId(null)}}/>
		  <section className='flex justify-center  w-full min-w-0'>
	  		{loginWindow && <Login finishLogin={()=>{location.reload()}}/>}
			<Background expanded={expanded}/>
			  <Chat expanded={expanded} setExpanded={setExpanded} chat_id={chat_id} setChatID={setChatId}/> 
			</section>
			<AnimatePresence>	  
	  		  {search && <SearchChat remove={()=>{setSearch(false)}}/>}
	        </AnimatePresence>
		</div>
  )
}

export default App
