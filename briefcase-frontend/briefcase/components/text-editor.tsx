'use client'

import * as React from 'react'
import { Bot, ChevronLeft, ChevronRight, FileText, FolderTree, Plus, Send, Settings, X } from 'lucide-react'
import { cn } from '@/lib/utils'

import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

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

export function TextEditor() {
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
                  <ScrollArea className="h-[calc(100vh-10rem)]">
                    <div className="space-y-4 p-4">
                      {files.map((folder) => (
                        <div key={folder.name}>
                          <div className="flex items-center gap-2 py-2">
                            <FolderTree className="h-4 w-4" />
                            <span className="text-sm font-medium">{folder.name}</span>
                          </div>
                          <div className="ml-4 space-y-2 border-l pl-3">
                            {folder.files.map((file) => (
                              <div key={file.name} className="flex items-center gap-2 rounded-md p-2 hover:bg-accent">
                                <FileText className="h-4 w-4" />
                                <span className="text-sm">{file.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                  <div className="p-4">
                    <Button variant="outline" className="w-full justify-start gap-2">
                      <Plus className="h-4 w-4" />
                      add files
                    </Button>
                  </div>
                </TabsContent>
                <TabsContent value="knowledge">
                  <div className="p-4 text-sm">knowledge base content</div>
                </TabsContent>
                <TabsContent value="settings">
                  <div className="p-4 text-sm">settings content</div>
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
            <div className="flex h-full flex-col">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
                <TabsList className="w-full justify-start rounded-none border-b bg-background p-0">
                  {openTabs.map((tab) => (
                    <TabsTrigger
                      key={tab.id}
                      value={tab.id}
                      className="relative rounded-none border-r data-[state=active]:bg-muted"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        {tab.title}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 rounded-sm p-0 hover:bg-accent"
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpenTabs(openTabs.filter((t) => t.id !== tab.id))
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    </TabsTrigger>
                  ))}
                </TabsList>
                {openTabs.map((tab) => (
                  <TabsContent key={tab.id} value={tab.id} className="h-full border-0 p-0">
                    <div className="h-full rounded-lg border p-4">
                      {/* Slate.js editor would go here */}
                      <div className="text-sm text-muted-foreground">
                        editor content for {tab.title}
                      </div>
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </div>
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
            <Card className="flex h-full flex-col rounded-none border-0 bg-transparent">
              <CardHeader>
                <CardTitle className="text-lg font-medium">document assistant</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden">
                <ScrollArea className="h-[calc(100vh-14rem)]">
                  <div className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      how can i help you today?
                    </div>
                  </div>
                </ScrollArea>
              </CardContent>
              <div className="p-4">
                <div className="flex gap-2">
                  <Input placeholder="type your message..." className="flex-1" />
                  <Button size="icon"><Send className="h-4 w-4" /></Button>
                </div>
              </div>
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
            </Card>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}