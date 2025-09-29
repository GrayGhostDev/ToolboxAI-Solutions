import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Classes Page Object Model
 * Handles class management and interactions
 */
export class ClassesPage extends BasePage {
  // Page elements
  private pageTitle: Locator;
  private createClassButton: Locator;
  private searchBar: Locator;
  private filterDropdown: Locator;
  private classGrid: Locator;
  private classList: Locator;
  private viewToggle: Locator;

  // Create class modal
  private modal: {
    container: Locator;
    nameInput: Locator;
    descriptionInput: Locator;
    subjectSelect: Locator;
    gradeSelect: Locator;
    capacityInput: Locator;
    startDateInput: Locator;
    endDateInput: Locator;
    saveButton: Locator;
    cancelButton: Locator;
  };

  // Class card elements
  private classCard: {
    title: Locator;
    description: Locator;
    studentCount: Locator;
    editButton: Locator;
    deleteButton: Locator;
    viewButton: Locator;
  };

  constructor(page: Page) {
    super(page);

    // Initialize page elements
    this.pageTitle = page.locator('[data-testid="page-title"]');
    this.createClassButton = page.locator('[data-testid="create-class-button"]');
    this.searchBar = page.locator('[data-testid="class-search"]');
    this.filterDropdown = page.locator('[data-testid="class-filter"]');
    this.classGrid = page.locator('[data-testid="class-grid"]');
    this.classList = page.locator('[data-testid="class-list"]');
    this.viewToggle = page.locator('[data-testid="view-toggle"]');

    // Initialize modal elements
    this.modal = {
      container: page.locator('[data-testid="create-class-modal"]'),
      nameInput: page.locator('[data-testid="class-name-input"]'),
      descriptionInput: page.locator('[data-testid="class-description-input"]'),
      subjectSelect: page.locator('[data-testid="class-subject-select"]'),
      gradeSelect: page.locator('[data-testid="class-grade-select"]'),
      capacityInput: page.locator('[data-testid="class-capacity-input"]'),
      startDateInput: page.locator('[data-testid="class-start-date"]'),
      endDateInput: page.locator('[data-testid="class-end-date"]'),
      saveButton: page.locator('[data-testid="save-class-button"]'),
      cancelButton: page.locator('[data-testid="cancel-class-button"]')
    };

    // Initialize class card elements (for first card)
    this.classCard = {
      title: page.locator('.class-card').first().locator('.class-title'),
      description: page.locator('.class-card').first().locator('.class-description'),
      studentCount: page.locator('.class-card').first().locator('.student-count'),
      editButton: page.locator('.class-card').first().locator('[data-testid="edit-class"]'),
      deleteButton: page.locator('.class-card').first().locator('[data-testid="delete-class"]'),
      viewButton: page.locator('.class-card').first().locator('[data-testid="view-class"]')
    };
  }

  /**
   * Navigate to classes page
   */
  async goto(): Promise<void> {
    await this.navigate('/classes');
    await this.waitForPageLoad();
  }

  /**
   * Create a new class
   */
  async createClass(classData: {
    name: string;
    description?: string;
    subject?: string;
    grade?: string;
    capacity?: number;
    startDate?: string;
    endDate?: string;
  }): Promise<void> {
    await this.createClassButton.click();
    await this.modal.container.waitFor({ state: 'visible' });

    // Fill in class details
    await this.fillInput(this.modal.nameInput, classData.name);

    if (classData.description) {
      await this.fillInput(this.modal.descriptionInput, classData.description);
    }

    if (classData.subject) {
      await this.modal.subjectSelect.selectOption(classData.subject);
    }

    if (classData.grade) {
      await this.modal.gradeSelect.selectOption(classData.grade);
    }

    if (classData.capacity) {
      await this.fillInput(this.modal.capacityInput, classData.capacity.toString());
    }

    if (classData.startDate) {
      await this.fillInput(this.modal.startDateInput, classData.startDate);
    }

    if (classData.endDate) {
      await this.fillInput(this.modal.endDateInput, classData.endDate);
    }

    // Save the class
    await this.modal.saveButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
    await this.modal.container.waitFor({ state: 'hidden' });
  }

  /**
   * Search for a class
   */
  async searchClass(query: string): Promise<void> {
    await this.fillInput(this.searchBar, query);
    await this.page.keyboard.press('Enter');
    await this.waitForAPIResponse('/api/v1/classes/search');
  }

  /**
   * Filter classes
   */
  async filterClasses(filter: 'all' | 'active' | 'archived' | 'upcoming'): Promise<void> {
    await this.filterDropdown.selectOption(filter);
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * Toggle view between grid and list
   */
  async toggleView(): Promise<void> {
    await this.viewToggle.click();
    await this.page.waitForTimeout(300); // Wait for animation
  }

  /**
   * Get all class cards
   */
  async getAllClasses(): Promise<Array<{
    title: string;
    description: string;
    studentCount: string;
  }>> {
    const cards = await this.page.locator('.class-card').all();
    const classes = [];

    for (const card of cards) {
      const title = await card.locator('.class-title').textContent();
      const description = await card.locator('.class-description').textContent();
      const studentCount = await card.locator('.student-count').textContent();

      classes.push({
        title: title || '',
        description: description || '',
        studentCount: studentCount || ''
      });
    }

    return classes;
  }

  /**
   * Get class count
   */
  async getClassCount(): Promise<number> {
    const cards = await this.page.locator('.class-card').all();
    return cards.length;
  }

  /**
   * Edit a class by index
   */
  async editClass(index: number, updates: Partial<{
    name: string;
    description: string;
    capacity: number;
  }>): Promise<void> {
    const editButton = this.page.locator('.class-card').nth(index).locator('[data-testid="edit-class"]');
    await editButton.click();
    await this.modal.container.waitFor({ state: 'visible' });

    if (updates.name) {
      await this.modal.nameInput.clear();
      await this.fillInput(this.modal.nameInput, updates.name);
    }

    if (updates.description) {
      await this.modal.descriptionInput.clear();
      await this.fillInput(this.modal.descriptionInput, updates.description);
    }

    if (updates.capacity) {
      await this.modal.capacityInput.clear();
      await this.fillInput(this.modal.capacityInput, updates.capacity.toString());
    }

    await this.modal.saveButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
    await this.modal.container.waitFor({ state: 'hidden' });
  }

  /**
   * Delete a class by index
   */
  async deleteClass(index: number): Promise<void> {
    const deleteButton = this.page.locator('.class-card').nth(index).locator('[data-testid="delete-class"]');
    await deleteButton.click();

    // Confirm deletion
    const confirmButton = this.page.locator('[data-testid="confirm-delete"]');
    await confirmButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * View class details
   */
  async viewClassDetails(index: number): Promise<void> {
    const viewButton = this.page.locator('.class-card').nth(index).locator('[data-testid="view-class"]');
    await viewButton.click();
    await this.page.waitForURL(/classes\/\d+/);
  }

  /**
   * Add students to a class
   */
  async addStudentsToClass(classIndex: number, studentIds: string[]): Promise<void> {
    await this.viewClassDetails(classIndex);

    const addStudentsButton = this.page.locator('[data-testid="add-students-button"]');
    await addStudentsButton.click();

    const studentModal = this.page.locator('[data-testid="add-students-modal"]');
    await studentModal.waitFor({ state: 'visible' });

    // Select students
    for (const studentId of studentIds) {
      const studentCheckbox = this.page.locator(`[data-student-id="${studentId}"]`);
      await studentCheckbox.check();
    }

    const addButton = this.page.locator('[data-testid="confirm-add-students"]');
    await addButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * Export class list
   */
  async exportClassList(format: 'csv' | 'pdf' | 'excel'): Promise<void> {
    const exportButton = this.page.locator('[data-testid="export-button"]');
    await exportButton.click();

    const formatOption = this.page.locator(`[data-testid="export-${format}"]`);
    await formatOption.click();

    // Wait for download
    const download = await this.page.waitForEvent('download');
    await download.saveAs(`downloads/classes.${format}`);
  }

  /**
   * Check if empty state is displayed
   */
  async hasEmptyState(): Promise<boolean> {
    const emptyState = this.page.locator('[data-testid="empty-state"]');
    return await this.isElementVisible(emptyState);
  }

  /**
   * Get pagination info
   */
  async getPaginationInfo(): Promise<{
    currentPage: number;
    totalPages: number;
    totalItems: number;
  }> {
    const pagination = this.page.locator('[data-testid="pagination"]');
    const currentPage = await pagination.locator('.current-page').textContent();
    const totalPages = await pagination.locator('.total-pages').textContent();
    const totalItems = await pagination.locator('.total-items').textContent();

    return {
      currentPage: parseInt(currentPage || '1'),
      totalPages: parseInt(totalPages || '1'),
      totalItems: parseInt(totalItems || '0')
    };
  }

  /**
   * Navigate to next page
   */
  async goToNextPage(): Promise<void> {
    const nextButton = this.page.locator('[data-testid="pagination-next"]');
    await nextButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * Navigate to previous page
   */
  async goToPreviousPage(): Promise<void> {
    const prevButton = this.page.locator('[data-testid="pagination-prev"]');
    await prevButton.click();
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * Sort classes
   */
  async sortBy(criteria: 'name' | 'date' | 'students'): Promise<void> {
    const sortDropdown = this.page.locator('[data-testid="sort-dropdown"]');
    await sortDropdown.selectOption(criteria);
    await this.waitForAPIResponse('/api/v1/classes');
  }

  /**
   * Validate class creation
   */
  async validateClassCreation(className: string): Promise<boolean> {
    await this.searchClass(className);
    const classes = await this.getAllClasses();
    return classes.some(c => c.title.includes(className));
  }
}