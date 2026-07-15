import Sidebar from './components/Sidebar'
import Background from './components/Background'
import Chat from './components/Chat'
import SearchChat from './components/SearchChat'
import { useState } from 'react'
import { AnimatePresence } from 'framer-motion'
function App() {
	const [expanded, setExpanded] = useState(false)
	const [search, setSearch] = useState(false)


  return (
		<div className='flex'>
		  <Sidebar search={()=>{setSearch(true)}}/>
		  <section className='flex justify-center  w-full relative '>
			<Background expanded={expanded}/>
			  <Chat expanded={expanded} setExpanded={setExpanded}/> 
			</section>
			<AnimatePresence>	  
	  		  {search && <SearchChat remove={()=>{setSearch(false)}}/>}
	        </AnimatePresence>
		</div>
  )
}

export default App
