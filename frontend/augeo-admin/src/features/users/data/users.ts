import { faker } from '@faker-js/faker'

// Set a fixed seed for consistent data generation
faker.seed(67890)

export const users = Array.from({ length: 500 }, () => {
  const first_name = faker.person.firstName()
  const last_name = faker.person.lastName()
  return {
    id: faker.string.uuid(),
    email: faker.internet.email({ firstName: first_name }).toLocaleLowerCase(),
    first_name,
    last_name,
    phone: faker.phone.number({ style: 'international' }),
    role: faker.helpers.arrayElement([
      'super_admin',
      'npo_admin',
      'event_coordinator',
      'staff',
      'donor',
    ]),
    npo_id: faker.helpers.arrayElement([null, faker.string.uuid()]),
    email_verified: faker.datatype.boolean(),
    is_active: faker.datatype.boolean({ probability: 0.9 }),
    last_login_at: faker.helpers.arrayElement([
      null,
      faker.date.recent().toISOString(),
    ]),
    created_at: faker.date.past().toISOString(),
    updated_at: faker.date.recent().toISOString(),
  }
})
