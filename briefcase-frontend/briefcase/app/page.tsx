'use client'

import * as React from 'react'
import { Bot, ChevronLeft, ChevronRight, FolderTree, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileBrowser } from '@/components/file-browser'
import { Editor } from '@/components/editor'
import { Assistant } from '@/components/assistant'
import { KnowledgeBase } from '@/components/knowledge-base'
import { Settings as SettingsComponent } from '@/components/settings'

// Sample data structure for files
const files = [
  {
    name: 'documents',
    files: [
      { name: 'project proposal.md' },
      { name: 'meeting notes.md' },
      { name: 'research paper.md' },
    ],
  },
  {
    name: 'images',
    files: [
      { name: 'screenshot.png' },
      { name: 'diagram.png' },
    ],
  },
]

export default function Page() {
  const [activeTab, setActiveTab] = React.useState('doc-1')
  const [openTabs, setOpenTabs] = React.useState([
    { id: 'doc-1', title: 'project proposal.md' },
    { id: 'doc-2', title: 'meeting notes.md' },
    { id: 'doc-3', title: 'research paper.md' },
  ])
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = React.useState(false)
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = React.useState(false)
  const [activeLeftTab, setActiveLeftTab] = React.useState('files')

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background font-sans lowercase text-foreground dark">
      <header className="flex h-14 items-center gap-4 border-b bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <h1 className="text-xl font-semibold">briefcase</h1>
      </header>
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel
            defaultSize={20}
            minSize={5}
            maxSize={25}
            collapsible={true}
            collapsedSize={5}
            onCollapse={() => setLeftSidebarCollapsed(true)}
            onExpand={() => setLeftSidebarCollapsed(false)}
            className={cn(
              "bg-muted/50",
              leftSidebarCollapsed && "min-w-[50px] transition-all duration-300 ease-in-out"
            )}
          >
            <div className="flex h-full flex-col">
              <Tabs value={activeLeftTab} onValueChange={setActiveLeftTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="files"><FolderTree className="h-4 w-4" /></TabsTrigger>
                  <TabsTrigger value="knowledge"><Bot className="h-4 w-4" /></TabsTrigger>
                  <TabsTrigger value="settings"><Settings className="h-4 w-4" /></TabsTrigger>
                </TabsList>
                <TabsContent value="files" className="flex-1 overflow-hidden">
                  <FileBrowser files={files} />
                </TabsContent>
                <TabsContent value="knowledge">
                  <KnowledgeBase />
                </TabsContent>
                <TabsContent value="settings">
                  <SettingsComponent />
                </TabsContent>
              </Tabs>
              <div className="mt-auto p-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="w-full"
                  onClick={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
                >
                  {leftSidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={55}>
            <Editor 
              activeTab={activeTab}
              openTabs={openTabs}
              onTabChange={setActiveTab}
              onTabClose={(tabId) => setOpenTabs(openTabs.filter((t) => t.id !== tabId))}
            />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel
            defaultSize={25}
            minSize={10}
            maxSize={30}
            collapsible={true}
            collapsedSize={5}
            onCollapse={() => setRightSidebarCollapsed(true)}
            onExpand={() => setRightSidebarCollapsed(false)}
            className={cn(
              "bg-muted/50",
              rightSidebarCollapsed && "min-w-[50px] transition-all duration-300 ease-in-out"
            )}
          >
            <Assistant />
            <div className="mt-auto p-2">
              <Button
                variant="ghost"
                size="icon"
                className="w-full"
                onClick={() => setRightSidebarCollapsed(!rightSidebarCollapsed)}
              >
                {rightSidebarCollapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}