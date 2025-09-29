import * as React from "react";
import { Box, Card, Text, Button, Table, Paper, Badge, ActionIcon, Stack, TextInput, Modal, Group } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { useState } from "react";
import {
  listSchools,
  createSchool,
  updateSchool,
  deleteSchool,
  activateSchool,
  type School as SchoolType,
  type SchoolCreate,
} from "../../../services/api";
import { useRealTimeData } from "../../../hooks/useRealTimeData";
import { IconPlus, IconEdit, IconTrash, IconSchool } from "@tabler/icons-react";

interface SchoolFormData {
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone?: string;
  email?: string;
  principal_name?: string;
  district?: string;
  max_students: number;
}

export default function Schools() {
  // Use real-time data hook
  const {
    data: schools,
    loading,
    error,
    create: createSchoolOptimistic,
    update: updateSchoolOptimistic,
    remove: removeSchoolOptimistic,
    refresh: fetchSchools
  } = useRealTimeData<SchoolType>({
    fetchFn: () => listSchools({ search: searchTerm }),
    createFn: createSchool,
    updateFn: updateSchool,
    deleteFn: deleteSchool,
    channel: 'schools_updates'
  });

  const [openDialog, setOpenDialog] = useState(false);
  const [editingSchool, setEditingSchool] = useState<SchoolType | null>(null);
  const [formData, setFormData] = useState<SchoolFormData>({
    name: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
    email: "",
    principal_name: "",
    district: "",
    max_students: 500,
  });
  const [searchTerm, setSearchTerm] = useState("");

  // Refetch when search term changes
  React.useEffect(() => {
    fetchSchools();
  }, [searchTerm, fetchSchools]);

  const handleAdd = () => {
    setEditingSchool(null);
    setFormData({
      name: "",
      address: "",
      city: "",
      state: "",
      zip_code: "",
      phone: "",
      email: "",
      principal_name: "",
      district: "",
      max_students: 500,
    });
    setOpenDialog(true);
  };

  const handleEdit = (school: SchoolType) => {
    setEditingSchool(school);
    setFormData({
      name: school.name,
      address: school.address,
      city: school.city,
      state: school.state,
      zip_code: school.zip_code,
      phone: school.phone || "",
      email: school.email || "",
      principal_name: school.principal_name || "",
      district: school.district || "",
      max_students: school.max_students,
    });
    setOpenDialog(true);
  };

  const handleSave = async () => {
    try {
      const schoolData: SchoolCreate = {
        ...formData,
        is_active: true,
      };

      if (editingSchool) {
        // Update existing school with optimistic update
        await updateSchoolOptimistic(editingSchool.id, schoolData);
      } else {
        // Create new school with optimistic update
        await createSchoolOptimistic(schoolData);
      }
      
      setOpenDialog(false);
    } catch (err) {
      console.error("Error saving school:", err);
      // Error handling is done by the real-time hook
    }
  };

  const handleDelete = async (schoolId: string) => {
    // The confirmation and error handling is done by the real-time hook
    await removeSchoolOptimistic(schoolId);
  };

  return (
    <Box>
      <Group justify="space-between" mb="lg">
        <Text size="xl" fw={600}>
          Schools Management
        </Text>
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={handleAdd}
        >
          Add School
        </Button>
      </Group>

      <Card>
        {error && (
          <Box mb="md" p="md" style={{ backgroundColor: 'var(--mantine-color-red-1)', borderRadius: 'var(--mantine-radius-sm)' }}>
            <Text c="red">{error}</Text>
          </Box>
        )}

        <Table.ScrollContainer minWidth={800}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>School Name</Table.Th>
                <Table.Th>Address</Table.Th>
                <Table.Th>Students</Table.Th>
                <Table.Th>Teachers</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Created</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {loading && schools.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={7} ta="center">
                    <Text>Loading schools...</Text>
                  </Table.Td>
                </Table.Tr>
              ) : schools.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={7} ta="center">
                    <Text>No schools found. Add your first school!</Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                schools.map((school) => (
                  <Table.Tr key={school.id}>
                    <Table.Td>
                      <Group gap="xs">
                        <IconSchool size={16} />
                        <Text fw={500}>{school.name}</Text>
                      </Group>
                    </Table.Td>
                    <Table.Td>{school.address}</Table.Td>
                    <Table.Td>{school.studentCount || 0}</Table.Td>
                    <Table.Td>{school.teacherCount || 0}</Table.Td>
                    <Table.Td>
                      <Badge
                        color={school.status === "active" ? "green" : "gray"}
                        size="sm"
                      >
                        {school.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{school.createdAt}</Table.Td>
                    <Table.Td>
                      <Group gap="xs">
                        <ActionIcon
                          onClick={() => handleEdit(school)}
                          size="sm"
                          disabled={loading}
                          variant="subtle"
                        >
                          <IconEdit size={16} />
                        </ActionIcon>
                        <ActionIcon
                          onClick={() => handleDelete(school.id)}
                          size="sm"
                          color="red"
                          disabled={loading}
                          variant="subtle"
                        >
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Card>

      <Modal
        opened={openDialog}
        onClose={() => setOpenDialog(false)}
        title={editingSchool ? "Edit School" : "Add New School"}
        size="lg"
      >
        <Stack gap="md">
          <TextInput
            label="School Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            required
            withAsterisk
          />
          <TextInput
            label="Address"
            value={formData.address}
            onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
            required
            withAsterisk
          />
          <Group grow>
            <TextInput
              label="City"
              value={formData.city}
              onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
              required
              withAsterisk
            />
            <TextInput
              label="State"
              value={formData.state}
              onChange={(e) => setFormData(prev => ({ ...prev, state: e.target.value }))}
              required
              withAsterisk
              placeholder="e.g., CA"
            />
            <TextInput
              label="Zip Code"
              value={formData.zip_code}
              onChange={(e) => setFormData(prev => ({ ...prev, zip_code: e.target.value }))}
              required
              withAsterisk
              placeholder="e.g., 12345"
            />
          </Group>
          <Group grow>
            <TextInput
              label="Phone"
              value={formData.phone}
              onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              placeholder="Optional"
            />
            <TextInput
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              placeholder="Optional"
            />
          </Group>
          <Group grow>
            <TextInput
              label="Principal Name"
              value={formData.principal_name}
              onChange={(e) => setFormData(prev => ({ ...prev, principal_name: e.target.value }))}
              placeholder="Optional"
            />
            <TextInput
              label="District"
              value={formData.district}
              onChange={(e) => setFormData(prev => ({ ...prev, district: e.target.value }))}
              placeholder="Optional"
            />
          </Group>
          <TextInput
            label="Maximum Students"
            type="number"
            value={formData.max_students.toString()}
            onChange={(e) => setFormData(prev => ({ ...prev, max_students: parseInt(e.target.value) || 500 }))}
            min={1}
            max={10000}
          />

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => setOpenDialog(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading || !formData.name || !formData.address || !formData.city || !formData.state || !formData.zip_code}
              loading={loading}
            >
              {editingSchool ? "Update" : "Create"}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Box>
  );
}