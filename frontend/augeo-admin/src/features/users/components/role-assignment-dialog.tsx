import React from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Shield } from 'lucide-react'
import { useUpdateUserRole } from '../hooks/use-users'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { SelectDropdown } from '@/components/select-dropdown'
import { roles } from '../data/data'
import type { User } from '../api/users-api'

const formSchema = z.object({
  role: z.string().min(1, 'Role is required'),
  npo_id: z.string().optional(),
})

type RoleAssignmentForm = z.infer<typeof formSchema>

type RoleAssignmentDialogProps = {
  user: User | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function RoleAssignmentDialog({
  user,
  open,
  onOpenChange,
}: RoleAssignmentDialogProps) {
  const updateRoleMutation = useUpdateUserRole()

  const form = useForm<RoleAssignmentForm>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      role: user?.role || '',
      npo_id: user?.npo_id || '',
    },
  })

  // Update form when user changes
  React.useEffect(() => {
    if (user) {
      form.reset({
        role: user.role,
        npo_id: user.npo_id || '',
      })
    }
  }, [user, form])

  const selectedRole = form.watch('role')
  const requiresNpoId = ['npo_admin', 'event_coordinator'].includes(selectedRole)

  const onSubmit = async (values: RoleAssignmentForm) => {
    if (!user?.id) {
      // No user selected - dialog should not be open
      return
    }

    // Call mutation to update role
    await updateRoleMutation.mutateAsync({
      userId: user.id,
      data: {
        role: values.role,
        ...(requiresNpoId && values.npo_id ? { npo_id: values.npo_id } : {}),
      },
    })

    // Close dialog on success
    onOpenChange(false)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(state) => {
        if (user) {
          form.reset({
            role: user.role,
            npo_id: user.npo_id || '',
          })
        }
        onOpenChange(state)
      }}
    >
      <DialogContent className='sm:max-w-md'>
        <DialogHeader className='text-start'>
          <DialogTitle className='flex items-center gap-2'>
            <Shield /> Assign Role
          </DialogTitle>
          <DialogDescription>
            Change the role for {user?.first_name} {user?.last_name}. This will
            determine their access level and permissions.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            id='role-assignment-form'
            onSubmit={form.handleSubmit(onSubmit)}
            className='space-y-4'
          >
            <FormField
              control={form.control}
              name='role'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <SelectDropdown
                    defaultValue={field.value}
                    onValueChange={field.onChange}
                    placeholder='Select a role'
                    items={roles.map(({ label, value }) => ({
                      label,
                      value,
                    }))}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />
            {requiresNpoId && (
              <FormField
                control={form.control}
                name='npo_id'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>NPO ID</FormLabel>
                    <FormControl>
                      <Input
                        placeholder='Enter NPO UUID'
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Required for NPO Admin and Event Coordinator roles
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
          </form>
        </Form>
        <DialogFooter className='gap-y-2'>
          <DialogClose asChild>
            <Button variant='outline' disabled={updateRoleMutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <Button
            type='submit'
            form='role-assignment-form'
            disabled={updateRoleMutation.isPending}
          >
            {updateRoleMutation.isPending ? 'Updating...' : 'Update Role'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
