import { TestApp, UIHelpers } from '@baserow/test/helpers/testApp'
import PublicPage from '@baserow/modules/database/pages/publicGrid'
import flushPromises from 'flush-promises'

// Mock out debounce so we dont have to wait or simulate waiting for the various
// debounces in the search functionality.
jest.mock('lodash/debounce', () => jest.fn((fn) => fn))

describe('Public View Page Tests', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach(() => testApp.afterEach())

  test('Can see a publicly shared grid view', async () => {
    const { application, table, gridView } =
      await givenASingleSimpleTableInTheServer()

    const tableComponent = await testApp.mount(PublicPage, {
      params: {
        slug: 'test_slug'
      },
    })

    expect(tableComponent.html()).toContain('gridView.rowCount - 1')

    mockServer.creatingRowInTableReturns(table, {
      id: 2,
      order: '2.00000000000000000000',
      field_1: '',
      field_2: '',
      field_3: '',
      field_4: false,
    })

    const button = tableComponent.find('.grid-view__add-row')
    await button.trigger('click')

    expect(tableComponent.html()).toContain('gridView.rowCount - 2')
  })

  })

  async function givenASingleSimpleTableInTheServer() {
    const table = mockServer.createTable()
    const { application } = await mockServer.createAppAndGroup(table)
    const gridView = mockServer.createGridView(application, table)
    const fields = mockServer.createFields(application, table, [
      {
        name: 'Name',
        type: 'text',
        primary: true,
      },
      {
        name: 'Last name',
        type: 'text',
      },
      {
        name: 'Notes',
        type: 'long_text',
      },
      {
        name: 'Active',
        type: 'boolean',
      },
    ])

    mockServer.createRows(gridView, fields, [
      {
        id: 1,
        order: 0,
        field_1: 'name',
        field_2: 'last_name',
        field_3: 'notes',
        field_4: false,
      },
    ])
    return { application, table, gridView }
  }
})
