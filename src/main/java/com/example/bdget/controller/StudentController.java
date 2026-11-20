package com.example.bdget.controller;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.bdget.dto.StudentRequest;
import com.example.bdget.model.Student;
import com.example.bdget.service.StudentService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/students")
// CORS restringido a origenes explicitos (configurable), sin comodin "*"
@CrossOrigin(origins = "${app.cors.allowed-origins:http://localhost}")
public class StudentController {

    @Autowired
    private StudentService studentService;

    @GetMapping
    public List<Student> getAllStudents() {
        return studentService.getAllStudents();
    }

    @GetMapping("/{id}")
    public Optional<Student> getStudentById(@PathVariable Long id) {
        return studentService.getStudentById(id);
    }

    @GetMapping("/search")
    public List<Student> searchStudentsByName(@RequestParam String name) {
        return studentService.searchStudentsByName(name);
    }

    @PostMapping
    public Student creaStudent(@Valid @RequestBody StudentRequest request) {
        return studentService.createStudent(toEntity(request));
    }

    @PutMapping("/{id}")
    public Student updateStudent(@PathVariable Long id, @Valid @RequestBody StudentRequest request) {
        return studentService.updateStudent(id, toEntity(request));
    }

    @DeleteMapping("/{id}")
    public void deleteStudent(@PathVariable Long id) {
        studentService.deleteStudent(id);
    }

    private Student toEntity(StudentRequest request) {
        Student student = new Student();
        student.setName(request.getName());
        return student;
    }
}