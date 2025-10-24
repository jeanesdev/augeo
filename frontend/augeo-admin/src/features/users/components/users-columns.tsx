import { DataTableColumnHeader } from '@/components/data-table'
import { LongText } from '@/components/long-text'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'
import { type ColumnDef } from '@tanstack/react-table'
import { callTypes, roles } from '../data/data'
import { type User } from '../data/schema'
import { DataTableRowActions } from './data-table-row-actions'

export const usersColumns: ColumnDef<User>[] = [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && 'indeterminate')
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label='Select all'
        className='translate-y-[2px]'
      />
    ),
    meta: {
      className: cn('max-md:sticky start-0 z-10 rounded-tl-[inherit]'),
    },
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label='Select row'
        className='translate-y-[2px]'
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    id: 'fullName',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Name' />
    ),
    cell: ({ row }) => {
      const { first_name, last_name } = row.original
      const fullName = `${first_name} ${last_name}`
      return <LongText className='max-w-36 ps-3'>{fullName}</LongText>
    },
    meta: {
      className: cn(
        'drop-shadow-[0_1px_2px_rgb(0_0_0_/_0.1)] dark:drop-shadow-[0_1px_2px_rgb(255_255_255_/_0.1)]',
        'ps-0.5 max-md:sticky start-6 @4xl/content:table-cell @4xl/content:drop-shadow-none',
        'w-36'
      ),
    },
    enableHiding: false,
  },
  {
    accessorKey: 'email',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Email' />
    ),
    cell: ({ row }) => (
      <div className='w-fit ps-2 text-nowrap'>{row.getValue('email')}</div>
    ),
  },
  {
    accessorKey: 'email_verified',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Email Verified' />
    ),
    cell: ({ row }) => {
      const emailVerified = row.original.email_verified
      return (
        <div className='flex space-x-2'>
          <Badge
            variant='outline'
            className={cn('capitalize', emailVerified ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200')}
          >
            {emailVerified ? 'Verified' : 'Unverified'}
          </Badge>
        </div>
      )
    },
    filterFn: (row, _id, value) => {
      const emailVerified = row.original.email_verified
      const status = emailVerified ? 'verified' : 'unverified'
      return value.includes(status)
    },
    enableSorting: false,
  },
  {
    accessorKey: 'phone',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Phone Number' />
    ),
    cell: ({ row }) => {
      const phone = row.getValue('phone') as string | null
      if (!phone) return <div>—</div>

      // Format phone number for display
      const digits = phone.replace(/\D/g, '')

      // 10 digits: (XXX)XXX-XXXX
      if (digits.length === 10) {
        const formatted = `(${digits.slice(0, 3)})${digits.slice(3, 6)}-${digits.slice(6)}`
        return <div className='font-mono text-sm'>{formatted}</div>
      }

      // 11 digits starting with 1: +1(XXX)XXX-XXXX
      if (digits.length === 11 && digits.startsWith('1')) {
        const formatted = `+1(${digits.slice(1, 4)})${digits.slice(4, 7)}-${digits.slice(7)}`
        return <div className='font-mono text-sm'>{formatted}</div>
      }

      // Return as-is if not standard format
      return <div className='font-mono text-sm'>{phone}</div>
    },
    enableSorting: false,
  },
  {
    id: 'status',
    accessorKey: 'is_active',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Status' />
    ),
    cell: ({ row }) => {
      const isActive = row.original.is_active
      const status = isActive ? 'active' : 'inactive'
      const badgeColor = callTypes.get(status)
      return (
        <div className='flex space-x-2'>
          <Badge variant='outline' className={cn('capitalize', badgeColor)}>
            {status}
          </Badge>
        </div>
      )
    },
    filterFn: (row, _id, value) => {
      const isActive = row.original.is_active
      const status = isActive ? 'active' : 'inactive'
      return value.includes(status)
    },
    enableHiding: false,
    enableSorting: false,
  },
  {
    accessorKey: 'role',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title='Role' />
    ),
    cell: ({ row }) => {
      const { role } = row.original
      const userType = roles.find(({ value }) => value === role)

      if (!userType) {
        // Fallback for unknown roles - display the role string
        return <span className='text-sm'>{role}</span>
      }

      return (
        <div className='flex items-center gap-x-2'>
          {userType.icon && (
            <userType.icon size={16} className='text-muted-foreground' />
          )}
          <span className='text-sm'>{userType.label}</span>
        </div>
      )
    },
    filterFn: (row, _id, value) => {
      return value.includes(row.getValue('role'))
    },
    enableSorting: false,
    enableHiding: false,
  },
  {
    id: 'actions',
    cell: DataTableRowActions,
  },
]
