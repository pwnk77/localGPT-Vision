'use client'

import * as React from 'react'
import { FolderTree, FileText, Plus } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'

interface File {
  name: string
}

interface Folder {
  name: string
  files: File[]
}

interface FileBrowserProps {
  files: Folder[]
}

export function FileBrowser({ files }: FileBrowserProps) {
  return (
    <>
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
    </>
  )
}
