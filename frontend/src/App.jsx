import Sidebar from './components/Sidebar'
import TextThing from './components/TextThing'
import Background from './components/Background'
import Chat from './components/Chat'
import { useState } from 'react'
function App() {
	const [expanded, setExpanded] = useState(false)


  return (
    <div className='flex'>
	  <Sidebar/>
	  <section className='flex justify-center  w-full relative '>
	    <Background expanded={expanded}/>
	  	  <Chat expanded={expanded} setExpanded={setExpanded}/> 
	  	</section>
	</div>
  )
}

export default App
